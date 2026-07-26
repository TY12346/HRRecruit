from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import JobApplication
from apps.applications.serializers import build_resume_payload
from apps.jobs.models import JobPosting
from apps.interviews.models import Interview
from apps.notifications.email_service import send_job_offer_email
from apps.notifications.services import create_bulk_notifications, create_notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User
from .models import HiringDecision, JobHiringDecision, JobHiringDecisionItem, JobOffer
from .serializers import (
    HiringDecisionSerializer,
    HiringDecisionSubmitSerializer,
    HRDecisionReviewSerializer,
    JobOfferAcceptSerializer,
    JobOfferCreateSerializer,
    JobOfferDeclineSerializer,
    JobOfferReviewSerializer,
    JobOfferSerializer,
    JobHiringDecisionSerializer,
    JobDecisionReviewSerializer,
    JobDecisionSubmitSerializer,
)
from .services import (
    ELIGIBLE_DECISION_STATUSES,
    application_scorecard_progress,
    refresh_job_readiness,
)


def get_active_membership(user, role):
    return OrganizationMembership.objects.filter(
        user=user,
        role=role,
        status=OrganizationMembership.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    ).select_related('organization').first()


def organization_hr_heads(organization):
    return User.objects.filter(
        role=User.Role.HR_HEAD,
        is_active=True,
        organization_memberships__organization=organization,
        organization_memberships__role=OrganizationMembership.Role.HR_HEAD,
        organization_memberships__status=OrganizationMembership.Status.ACTIVE,
    ).distinct()


def base_decision_queryset():
    return HiringDecision.objects.select_related(
        'application',
        'application__job',
        'application__job__organization',
        'application__job__recruiter',
        'application__applicant',
        'application__applicant__applicant_profile',
        'application__assigned_interviewer',
        'recruiter',
        'hr_head',
    )


def visible_decisions_for(user):
    decisions = base_decision_queryset()
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        if membership:
            return decisions.filter(application__job__organization=membership.organization, recruiter=user)
    if user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
        if membership:
            return decisions.filter(application__job__organization=membership.organization)
    if user.role == User.Role.APPLICANT:
        return decisions.filter(application__applicant=user)
    return decisions.none()


def base_offer_queryset():
    return JobOffer.objects.select_related(
        'application',
        'application__job',
        'application__job__organization',
        'application__job__recruiter',
        'application__applicant',
        'application__applicant__applicant_profile',
        'application__assigned_interviewer',
    )


def visible_offers_for(user):
    offers = base_offer_queryset()
    if user.role == User.Role.APPLICANT:
        return offers.filter(
            application__applicant=user,
            offer_status__in=[
                JobOffer.OfferStatus.PENDING_APPLICANT_RESPONSE,
                JobOffer.OfferStatus.ACCEPTED,
                JobOffer.OfferStatus.REJECTED,
            ],
        )
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        if membership:
            return offers.filter(application__job__organization=membership.organization, application__job__recruiter=user)
    if user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
        if membership:
            return offers.filter(application__job__organization=membership.organization)
    return offers.none()


def recruiter_application_or_404(user, application_id):
    if user.role != User.Role.RECRUITER:
        raise PermissionDenied('Only recruiters can perform this action.')
    membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
    if not membership:
        raise PermissionDenied('Recruiter must belong to an active organization.')
    return get_object_or_404(
        JobApplication.objects.select_related('job', 'job__organization', 'job__recruiter', 'applicant'),
        id=application_id,
        job__organization=membership.organization,
        job__recruiter=user,
    )


def pending_decision_for_hr_head_or_404(user, decision_id):
    membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
    if not membership:
        raise PermissionDenied('An active hiring manager organization membership is required.')
    decision = get_object_or_404(
        HiringDecision.objects.select_for_update(),
        id=decision_id,
        status=HiringDecision.Status.PENDING_HR_APPROVAL,
    )
    if decision.application.job.organization_id != membership.organization_id:
        raise Http404('Hiring decision not found.')
    return decision


def recruiter_offer_for_update_or_404(user, offer_id):
    if user.role != User.Role.RECRUITER:
        raise PermissionDenied('Only recruiters can manage job offers.')
    membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
    if not membership:
        raise PermissionDenied('Recruiter must belong to an active organization.')
    return get_object_or_404(
        JobOffer.objects.select_for_update().select_related('application', 'application__job', 'application__applicant'),
        id=offer_id,
        application__job__organization=membership.organization,
        application__job__recruiter=user,
    )


def applicant_offer_for_update_or_404(user, offer_id):
    offer = get_object_or_404(JobOffer.objects.select_for_update(), id=offer_id)
    if offer.application.applicant_id != user.id:
        raise Http404('Job offer not found.')
    return offer


def hr_offer_for_update_or_404(user, offer_id):
    membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
    if not membership:
        raise PermissionDenied('An active hiring manager organization membership is required.')
    return get_object_or_404(
        JobOffer.objects.select_for_update().select_related('application', 'application__job', 'application__applicant'),
        id=offer_id, application__job__organization=membership.organization,
    )


def change_application_status(application, new_status, changed_by, note):
    return application.change_status(new_status, changed_by=changed_by, note=note)


def recruiter_job_or_404(user, job_id):
    if user.role != User.Role.RECRUITER:
        raise PermissionDenied('Only recruiters can submit hiring decisions.')
    membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
    if not membership:
        raise PermissionDenied('Recruiter must belong to an active organization.')
    return get_object_or_404(
        JobPosting.objects.select_related('organization', 'recruiter'),
        id=job_id, organization=membership.organization, recruiter=user,
    )


def decision_for_hr_or_404(user, decision_id):
    if user.role != User.Role.HR_HEAD:
        raise PermissionDenied('Only hiring managers can review hiring decisions.')
    membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
    if not membership:
        raise PermissionDenied('An active hiring manager organization membership is required.')
    return get_object_or_404(
        JobHiringDecision.objects.select_for_update().select_related('job_posting', 'recruiter'),
        id=decision_id, job_posting__organization=membership.organization,
        status=JobHiringDecision.Status.PENDING_HR_APPROVAL,
    )

# Recruiters may only request hiring manager approval after an interviewer has submitted
# the interview evaluation. This keeps the FYP demo workflow in the required
# interview -> evaluation -> hiring-decision order.
HIRING_DECISION_ELIGIBLE_APPLICATION_STATUSES = (JobApplication.Status.UNDER_REVIEW,)


class JobApplicantComparisonAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        if request.user.role == User.Role.RECRUITER:
            job = recruiter_job_or_404(request.user, job_id)
        elif request.user.role == User.Role.HR_HEAD:
            membership = get_active_membership(request.user, OrganizationMembership.Role.HR_HEAD)
            if not membership:
                raise PermissionDenied('An active hiring manager organization membership is required.')
            job = get_object_or_404(JobPosting, id=job_id, organization=membership.organization)
        else:
            raise PermissionDenied('Only recruiters and hiring managers can compare applicants.')

        readiness = refresh_job_readiness(job)
        applications = job.applications.select_related('applicant', 'assigned_interviewer').prefetch_related(
            'interviews__evaluations__interviewer',
            'interviews__evaluations__answers__criterion',
            'interviews__recordings__transcripts__ai_summaries',
        ).order_by('-final_score', 'applied_at')
        applicants = []
        for application in applications:
            interviews = list(application.interviews.all())
            evaluations = [evaluation for interview in interviews for evaluation in interview.evaluations.all()]
            scorecards = application_scorecard_progress(application)
            transcripts = [transcript for interview in interviews for recording in interview.recordings.all()
                           for transcript in recording.transcripts.all()]
            summaries = [summary for interview in interviews for recording in interview.recordings.all()
                         for transcript in recording.transcripts.all() for summary in transcript.ai_summaries.all()]
            applicants.append({
                'application_id': application.id,
                'applicant_name': application.applicant.full_name,
                'applicant_email': application.applicant.email,
                'applicant_phone': application.applicant.phone_number,
                'resume_url': build_resume_payload(application, {'request': request})['resume_url'],
                'application_status': application.status,
                'ai_resume_score': application.final_score,
                'matched_skills': application.score_explanation.get('matched_skills', []),
                'missing_skills': application.score_explanation.get('missing_skills', []),
                'extracted_skills': application.extracted_skills,
                'extracted_education': application.extracted_education,
                'extracted_experience': application.extracted_experience,
                'shortlisted': bool(interviews) or application.status in ELIGIBLE_DECISION_STATUSES,
                'interview_statuses': [interview.status for interview in interviews],
                'evaluation_status': (
                    'submitted' if scorecards['complete'] and (scorecards['has_completed_interviews'] or evaluations)
                    else ('not_required' if not interviews else 'pending')
                ),
                'scorecards_submitted': scorecards['submitted'],
                'scorecards_required': scorecards['required'],
                'evaluation_score': evaluations[-1].total_score if evaluations else None,
                'evaluation_summary': evaluations[-1].overall_comment if evaluations else '',
                'interviewer_remarks': [evaluation.overall_comment for evaluation in evaluations],
                'interviewer_remarks_detail': [
                    {
                        'interviewer_name': evaluation.interviewer.full_name or evaluation.interviewer.email,
                        'remark': evaluation.overall_comment,
                    }
                    for evaluation in evaluations
                ],
                'interviewer_evaluations': [
                    {
                        'interviewer_name': evaluation.interviewer.full_name or evaluation.interviewer.email,
                        'answers': [
                            {
                                'criterion_id': answer.criterion_id,
                                'criterion_name': answer.criterion.criterion_name,
                                'max_score': answer.criterion.max_score,
                                'score': answer.score,
                                'comment': answer.comment,
                            }
                            for answer in evaluation.answers.all()
                        ],
                    }
                    for evaluation in evaluations
                ],
                'interviews': [{'id': interview.id} for interview in interviews],
                'transcript_status': 'available' if transcripts else 'not_available',
                'ai_summary_status': 'available' if summaries else 'not_available',
                'ai_interview_summaries': [summary.editable_summary_text for summary in summaries],
                'recruiter_remark': application.recruiter_remark,
                'eligible_for_decision': (
                    application.status in HIRING_DECISION_ELIGIBLE_APPLICATION_STATUSES
                    and scorecards['complete']
                ),
            })
        return Response({'job': {'id': job.id, 'title': job.title, 'status': job.status, 'vacancies': job.vacancies},
                         'readiness': readiness, 'applicants': applicants})


class JobHiringDecisionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        decisions = JobHiringDecision.objects.select_related('job_posting', 'job_posting__organization', 'recruiter', 'reviewed_by').prefetch_related('items__application__applicant')
        if request.user.role == User.Role.RECRUITER:
            membership = get_active_membership(request.user, OrganizationMembership.Role.RECRUITER)
            decisions = decisions.filter(job_posting__organization=membership.organization, recruiter=request.user) if membership else decisions.none()
        elif request.user.role == User.Role.HR_HEAD:
            membership = get_active_membership(request.user, OrganizationMembership.Role.HR_HEAD)
            decisions = decisions.filter(job_posting__organization=membership.organization) if membership else decisions.none()
        else:
            raise PermissionDenied('Your role cannot access job-level hiring decisions.')
        if request.query_params.get('job_posting'):
            decisions = decisions.filter(job_posting_id=request.query_params['job_posting'])
        if request.query_params.get('status'):
            decisions = decisions.filter(status=request.query_params['status'])
        return Response(JobHiringDecisionSerializer(decisions, many=True, context={'request': request}).data)

    @transaction.atomic
    def post(self, request):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can submit hiring decisions.')
        serializer = JobDecisionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = recruiter_job_or_404(request.user, request.data.get('job_posting'))
        if JobHiringDecision.objects.filter(job_posting=job, status=JobHiringDecision.Status.PENDING_HR_APPROVAL).exists():
            raise ValidationError({'job_posting': 'This job already has a decision pending hiring manager approval.'})
        readiness = refresh_job_readiness(job)
        if not readiness['ready']:
            raise ValidationError({'readiness': readiness['reasons'] or ['Job is not ready for a hiring decision.']})

        decision_type = serializer.validated_data['decision_type']
        application_ids = serializer.validated_data['application_ids']
        if len(application_ids) != len(set(application_ids)):
            raise ValidationError({'application_ids': 'Each applicant can only be selected once.'})
        if decision_type == JobHiringDecision.DecisionType.RECOMMEND_HIRE:
            if not application_ids:
                raise ValidationError({'application_ids': 'Recommend Hire requires at least one selected applicant.'})
            if len(application_ids) > job.vacancies:
                raise ValidationError({'application_ids': f'No more than {job.vacancies} applicant(s) may be selected for this job.'})
        elif application_ids:
            raise ValidationError({'application_ids': 'Recommend No Hire must not select any applicants.'})
        applications = list(job.applications.filter(id__in=application_ids))
        if len(applications) != len(application_ids):
            raise ValidationError({'application_ids': 'Every selected applicant must belong to this job posting.'})
        invalid = [
            application.id for application in applications
            if application.status not in HIRING_DECISION_ELIGIBLE_APPLICATION_STATUSES
            or not application_scorecard_progress(application)['complete']
        ]
        if invalid:
            raise ValidationError({'application_ids': f'Selected applicants are not fully interviewed/evaluated: {invalid}.'})

        decision = JobHiringDecision.objects.create(
            job_posting=job, recruiter=request.user, decision_type=decision_type,
            justification=serializer.validated_data['justification'], status=JobHiringDecision.Status.PENDING_HR_APPROVAL,
            submitted_at=timezone.now(),
        )
        reasons = serializer.validated_data['reasons']
        JobHiringDecisionItem.objects.bulk_create([
            JobHiringDecisionItem(decision=decision, application=application,
                                        selection_order=index, reason=reasons.get(str(application.id), ''), selected_for_offer=True)
            for index, application in enumerate(applications, start=1)
        ])
        job.status = JobPosting.Status.CLOSED
        job.save(update_fields=['status', 'updated_at'])
        create_bulk_notifications(list(organization_hr_heads(job.organization)), 'hiring_decision_submitted',
                                  'Job-level hiring decision pending approval',
                                  f'{request.user.full_name} submitted a hiring decision for {job.title}.', related_entity=decision)
        return Response(JobHiringDecisionSerializer(decision, context={'request': request}).data, status=status.HTTP_201_CREATED)


class JobHiringDecisionApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, decision_id):
        decision = decision_for_hr_or_404(request.user, decision_id)
        serializer = JobDecisionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision.status = JobHiringDecision.Status.APPROVED
        decision.reviewed_by = request.user
        decision.reviewed_at = timezone.now()
        decision.hr_remarks = serializer.validated_data['hr_remarks']
        decision.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_remarks', 'updated_at'])
        job = decision.job_posting
        if decision.decision_type == JobHiringDecision.DecisionType.RECOMMEND_NO_HIRE:
            job.status = JobPosting.Status.CLOSED
        else:
            job.status = JobPosting.Status.CLOSED
            for item in decision.items.select_related('application'):
                change_application_status(item.application, JobApplication.Status.UNDER_REVIEW, request.user, 'Selected in approved job-level hiring decision.')
        job.save(update_fields=['status', 'updated_at'])
        create_notification(decision.recruiter, 'hiring_decision_reviewed', 'Hiring decision approved',
                            f'Hiring manager approved the hiring decision for {job.title}.', related_entity=decision)
        return Response(JobHiringDecisionSerializer(decision, context={'request': request}).data)


class JobHiringDecisionRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, decision_id):
        decision = decision_for_hr_or_404(request.user, decision_id)
        serializer = JobDecisionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision.status = JobHiringDecision.Status.REJECTED
        decision.reviewed_by = request.user
        decision.reviewed_at = timezone.now()
        decision.hr_remarks = serializer.validated_data['hr_remarks']
        decision.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'hr_remarks', 'updated_at'])
        job = decision.job_posting
        job.status = JobPosting.Status.CLOSED
        job.save(update_fields=['status', 'updated_at'])
        create_notification(decision.recruiter, 'hiring_decision_reviewed', 'Hiring decision returned for review',
                            f'Hiring manager rejected the hiring decision for {job.title}.', related_entity=decision)
        return Response(JobHiringDecisionSerializer(decision, context={'request': request}).data)


class HiringDecisionSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        raise ValidationError({
            'detail': (
                'Applicant-level hiring decisions are no longer accepted. Close application intake and submit '
                'one job-level Hiring Decision.'
            )
        })


class PendingHiringDecisionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.HR_HEAD:
            raise PermissionDenied('Only hiring managers can view pending hiring decisions.')
        decisions = visible_decisions_for(request.user).filter(status=HiringDecision.Status.PENDING_HR_APPROVAL)
        return Response(HiringDecisionSerializer(decisions, many=True, context={'request': request}).data)


class HiringDecisionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):
        decision = get_object_or_404(visible_decisions_for(request.user), id=decision_id)
        return Response(HiringDecisionSerializer(decision, context={'request': request}).data)


class HiringDecisionApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, decision_id):
        if request.user.role != User.Role.HR_HEAD:
            raise PermissionDenied('Only hiring managers can approve hiring decisions.')
        decision = pending_decision_for_hr_head_or_404(request.user, decision_id)
        serializer = HRDecisionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        decision.status = HiringDecision.Status.APPROVED
        decision.hr_head = request.user
        decision.hr_head_justification = serializer.validated_data['justification']
        decision.reviewed_at = timezone.now()
        decision.save(update_fields=['status', 'hr_head', 'hr_head_justification', 'reviewed_at'])

        application = decision.application
        if decision.decision == HiringDecision.Decision.HIRE:
            new_status = JobApplication.Status.UNDER_REVIEW
            note = f'Hiring manager approved hire decision: {decision.hr_head_justification}'
        else:
            new_status = JobApplication.Status.REJECTED
            note = f'Hiring manager approved reject decision: {decision.hr_head_justification}'
        change_application_status(application, new_status, request.user, note)
        create_notification(
            decision.recruiter,
            'hiring_decision_reviewed',
            'Hiring decision approved',
            f'Hiring manager approved your {decision.decision} decision for {application.applicant.full_name}.',
            related_entity=decision,
        )
        if decision.decision == HiringDecision.Decision.REJECT:
            create_notification(
                application.applicant,
                'application_status_update',
                'Application status updated',
                f'Your application for {application.job.title} was not selected.',
                related_entity=application,
            )
        return Response(HiringDecisionSerializer(decision, context={'request': request}).data)


class HiringDecisionRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, decision_id):
        if request.user.role != User.Role.HR_HEAD:
            raise PermissionDenied('Only hiring managers can reject hiring decisions.')
        decision = pending_decision_for_hr_head_or_404(request.user, decision_id)
        serializer = HRDecisionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        decision.status = HiringDecision.Status.REJECTED
        decision.hr_head = request.user
        decision.hr_head_justification = serializer.validated_data['justification']
        decision.reviewed_at = timezone.now()
        decision.save(update_fields=['status', 'hr_head', 'hr_head_justification', 'reviewed_at'])

        application = decision.application
        change_application_status(
            application,
            JobApplication.Status.REJECTED,
            request.user,
            f'Hiring manager rejected {decision.decision} decision: {decision.hr_head_justification}',
        )
        create_notification(
            decision.recruiter,
            'hiring_decision_reviewed',
            'Hiring decision rejected by HR',
            f'Hiring manager rejected your {decision.decision} decision for {application.applicant.full_name}.',
            related_entity=decision,
        )
        return Response(HiringDecisionSerializer(decision, context={'request': request}).data)


class JobOfferCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request, application_id):
        application = recruiter_application_or_404(request.user, application_id)
        approved_hire_exists = JobHiringDecisionItem.objects.filter(
            application=application,
            selected_for_offer=True,
            decision__recruiter=request.user,
            decision__decision_type=JobHiringDecision.DecisionType.RECOMMEND_HIRE,
            decision__status=JobHiringDecision.Status.APPROVED,
        ).exists()
        if not approved_hire_exists or application.status != JobApplication.Status.UNDER_REVIEW:
            raise ValidationError({'application': 'A job offer can only be sent to a applicant selected in an HR-approved job-level hiring decision.'})
        if JobOffer.objects.filter(application=application).exists():
            raise ValidationError({'application': 'This application already has a job offer. Edit and resubmit a disapproved offer instead.'})

        serializer = JobOfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer = JobOffer.objects.create(
            application=application, offer_status=JobOffer.OfferStatus.PENDING_APPROVAL,
            **serializer.validated_data,
        )
        create_bulk_notifications(
            list(organization_hr_heads(application.job.organization)),
            'job_offer_approval_requested',
            'Job offer pending approval',
            f'{request.user.full_name} submitted a job offer for {application.applicant.full_name}.',
            related_entity=offer,
        )
        return Response(JobOfferSerializer(offer, context={'request': request}).data, status=status.HTTP_201_CREATED)


class JobOfferListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = visible_offers_for(request.user)
        job_posting = request.query_params.get('job_posting')
        if job_posting:
            if not job_posting.isdigit():
                raise ValidationError({'job_posting': 'A valid job posting id is required.'})
            offers = offers.filter(application__job_id=job_posting)
        return Response(JobOfferSerializer(offers, many=True, context={'request': request}).data)


class JobOfferApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, offer_id):
        offer = hr_offer_for_update_or_404(request.user, offer_id)
        if offer.offer_status != JobOffer.OfferStatus.PENDING_APPROVAL:
            raise ValidationError({'offer_status': 'Only offers pending approval can be approved.'})
        serializer = JobOfferReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer.offer_status = JobOffer.OfferStatus.APPROVED
        offer.reviewed_by = request.user
        offer.reviewed_at = timezone.now()
        offer.hiring_manager_remarks = serializer.validated_data['remarks']
        offer.save(update_fields=['offer_status', 'reviewed_by', 'reviewed_at', 'hiring_manager_remarks'])
        create_notification(offer.application.job.recruiter, 'job_offer_reviewed', 'Job offer approved',
                            f'The job offer for {offer.application.applicant.full_name} was approved. Send it to the applicant when ready.', related_entity=offer)
        return Response(JobOfferSerializer(offer, context={'request': request}).data)


class JobOfferDisapproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, offer_id):
        offer = hr_offer_for_update_or_404(request.user, offer_id)
        if offer.offer_status != JobOffer.OfferStatus.PENDING_APPROVAL:
            raise ValidationError({'offer_status': 'Only offers pending approval can be disapproved.'})
        serializer = JobOfferReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data['remarks']:
            raise ValidationError({'remarks': 'A reason is required when disapproving an offer.'})
        offer.offer_status = JobOffer.OfferStatus.DISAPPROVED
        offer.reviewed_by = request.user
        offer.reviewed_at = timezone.now()
        offer.hiring_manager_remarks = serializer.validated_data['remarks']
        offer.save(update_fields=['offer_status', 'reviewed_by', 'reviewed_at', 'hiring_manager_remarks'])
        create_notification(offer.application.job.recruiter, 'job_offer_reviewed', 'Job offer changes requested',
                            serializer.validated_data['remarks'], related_entity=offer)
        return Response(JobOfferSerializer(offer, context={'request': request}).data)


class JobOfferResubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def patch(self, request, offer_id):
        offer = recruiter_offer_for_update_or_404(request.user, offer_id)
        if offer.offer_status != JobOffer.OfferStatus.DISAPPROVED:
            raise ValidationError({'offer_status': 'Only disapproved offers can be edited and resubmitted.'})
        serializer = JobOfferCreateSerializer(offer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(offer, field, value)
        offer.offer_status = JobOffer.OfferStatus.PENDING_APPROVAL
        offer.reviewed_by = None
        offer.reviewed_at = None
        offer.save()
        create_bulk_notifications(list(organization_hr_heads(offer.application.job.organization)),
                                  'job_offer_approval_requested', 'Revised job offer pending approval',
                                  f'{request.user.full_name} resubmitted the offer for {offer.application.applicant.full_name}.', related_entity=offer)
        return Response(JobOfferSerializer(offer, context={'request': request}).data)


class JobOfferSendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, offer_id):
        offer = recruiter_offer_for_update_or_404(request.user, offer_id)
        if offer.offer_status != JobOffer.OfferStatus.APPROVED:
            raise ValidationError({'offer_status': 'Only hiring-manager-approved offers can be sent to applicants.'})
        offer.offer_status = JobOffer.OfferStatus.PENDING_APPLICANT_RESPONSE
        offer.sent_at = timezone.now()
        offer.save(update_fields=['offer_status', 'sent_at'])
        create_notification(offer.application.applicant, 'job_offer_sent', 'Job offer received', offer.offer_message, related_entity=offer)
        send_job_offer_email(offer)
        return Response(JobOfferSerializer(offer, context={'request': request}).data)


class JobOfferAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, offer_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can accept job offers.')
        offer = applicant_offer_for_update_or_404(request.user, offer_id)
        if offer.offer_status != JobOffer.OfferStatus.PENDING_APPLICANT_RESPONSE:
            raise ValidationError({'offer_status': 'Only sent job offers can be accepted.'})
        if offer.respond_deadline < timezone.now():
            offer.offer_status = JobOffer.OfferStatus.REJECTED
            offer.save(update_fields=['offer_status'])
            raise ValidationError({'respond_deadline': 'This job offer has expired.'})

        serializer = JobOfferAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        offer.offer_status = JobOffer.OfferStatus.ACCEPTED
        offer.responded_at = timezone.now()
        offer.applicant_response_note = serializer.validated_data.get('note', '')
        offer.save(update_fields=['offer_status', 'responded_at', 'applicant_response_note'])
        application = offer.application
        change_application_status(
            application,
            JobApplication.Status.UNDER_REVIEW,
            request.user,
            'Applicant accepted job offer; application marked as hired for final lifecycle and analytics.',
        )
        job = JobPosting.objects.select_for_update().get(pk=application.job_id)
        if job.vacancies <= 0:
            raise ValidationError({'vacancies': 'This job has no remaining vacancy.'})
        job.vacancies -= 1
        job.status = JobPosting.Status.CLOSED if job.vacancies == 0 else JobPosting.Status.OPEN
        job.save(update_fields=['vacancies', 'status', 'updated_at'])
        create_notification(
            application.job.recruiter,
            'offer_response',
            'Job offer accepted',
            f'{request.user.full_name} accepted the job offer for {application.job.title}.',
            related_entity=offer,
        )
        create_bulk_notifications(
            list(organization_hr_heads(application.job.organization)),
            'offer_response',
            'Job offer accepted',
            f'{request.user.full_name} accepted the job offer for {application.job.title}.',
            related_entity=offer,
        )
        return Response(JobOfferSerializer(offer, context={'request': request}).data)


class JobOfferDeclineAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, offer_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can decline job offers.')
        offer = applicant_offer_for_update_or_404(request.user, offer_id)
        if offer.offer_status != JobOffer.OfferStatus.PENDING_APPLICANT_RESPONSE:
            raise ValidationError({'offer_status': 'Only sent job offers can be declined.'})
        serializer = JobOfferDeclineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        offer.offer_status = JobOffer.OfferStatus.REJECTED
        offer.responded_at = timezone.now()
        offer.applicant_response_note = serializer.validated_data.get('reason', '')
        offer.save(update_fields=['offer_status', 'responded_at', 'applicant_response_note'])
        application = offer.application
        decline_note = serializer.validated_data.get('reason') or 'Applicant declined job offer.'
        change_application_status(application, JobApplication.Status.REJECTED, request.user, decline_note)
        application.job.status = JobPosting.Status.OPEN
        application.job.save(update_fields=['status', 'updated_at'])
        create_notification(
            application.job.recruiter,
            'offer_response',
            'Job offer declined',
            f'{request.user.full_name} declined the job offer for {application.job.title}.',
            related_entity=offer,
        )
        create_bulk_notifications(
            list(organization_hr_heads(application.job.organization)),
            'offer_response',
            'Job offer declined',
            f'{request.user.full_name} declined the job offer for {application.job.title}.',
            related_entity=offer,
        )
        return Response(JobOfferSerializer(offer, context={'request': request}).data)

class JobOfferWithdrawAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, offer_id):
        offer = recruiter_offer_for_update_or_404(request.user, offer_id)
        if offer.offer_status != JobOffer.OfferStatus.PENDING_APPLICANT_RESPONSE:
            raise ValidationError({'offer_status': 'Only sent job offers can be withdrawn.'})

        offer.offer_status = JobOffer.OfferStatus.REJECTED
        offer.withdrawn_at = timezone.now()
        offer.internal_notes = request.data.get('internal_notes', offer.internal_notes)
        offer.save(update_fields=['offer_status', 'withdrawn_at', 'internal_notes'])
        application = offer.application
        change_application_status(
            application,
            JobApplication.Status.UNDER_REVIEW,
            request.user,
            'Recruiter withdrew the sent job offer; applicant remains HR-approved for a revised offer.',
        )
        create_notification(
            application.applicant,
            'job_offer_withdrawn',
            'Job offer withdrawn',
            f'The job offer for {application.job.title} was withdrawn. The recruiter may contact you with an update.',
            related_entity=offer,
        )
        create_bulk_notifications(
            list(organization_hr_heads(application.job.organization)),
            'job_offer_withdrawn',
            'Job offer withdrawn',
            f'{request.user.full_name} withdrew the job offer for {application.applicant.full_name}.',
            related_entity=offer,
        )
        return Response(JobOfferSerializer(offer, context={'request': request}).data)
