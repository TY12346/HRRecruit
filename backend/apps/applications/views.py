"""Role-protected and organization-isolated job application APIs."""

from django.db import transaction
from django.http import FileResponse
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_services.resume_text_extractor import ResumeTextExtractionError
from apps.jobs.models import JobPosting
from apps.notifications.services import create_notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import ApplicantResume, User

from .models import ApplicationStageHistory, JobApplication
from .serializers import (
    ApplicationRejectSerializer,
    ApplicationRemarkSerializer,
    ApplicationShortlistSerializer,
    ApplicationStageHistorySerializer,
    CandidateProfileSerializer,
    JobApplicationSerializer,
)
from .services import screen_job_application


def get_application_resume_file(application):
    if getattr(application, 'resume_id', None) and application.resume and application.resume.resume_file:
        return application.resume.resume_file
    applicant_profile = getattr(application.applicant, 'applicant_profile', None)
    return getattr(applicant_profile, 'resume_file', None)


def select_applicant_resume(applicant, resume_id=None):
    if resume_id:
        try:
            return ApplicantResume.objects.get(id=resume_id, applicant=applicant)
        except ApplicantResume.DoesNotExist as exc:
            raise ValidationError({'resume_id': 'Select one of your uploaded resumes.'}) from exc
    return (
        applicant.resumes.filter(is_default=True).first()
        or applicant.resumes.order_by('-uploaded_at', '-id').first()
    )


def get_active_membership(user, role):
    return OrganizationMembership.objects.filter(
        user=user,
        role=role,
        status=OrganizationMembership.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    ).select_related('organization').first()


def visible_applications_for(user):
    applications = JobApplication.objects.select_related(
        'job', 'job__organization', 'job__recruiter', 'applicant', 'applicant__applicant_profile', 'resume'
    )
    if user.role == User.Role.APPLICANT:
        return applications.filter(applicant=user)
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        if membership:
            return applications.filter(job__organization=membership.organization, job__recruiter=user)
    elif user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
        if membership:
            return applications.filter(job__organization=membership.organization)
    return applications.none()


APPLICATION_SORT_OPTIONS = {
    'newest': ('-applied_at',),
    'oldest': ('applied_at',),
    'score_desc': (F('final_score').desc(nulls_last=True), 'applied_at'),
    'score_asc': (F('final_score').asc(nulls_last=True), 'applied_at'),
    'candidate_az': ('applicant__full_name', 'applicant__email', '-applied_at'),
}


def parse_decimal_filter(value, field_name):
    if value in (None, ''):
        return None
    try:
        parsed = float(value)
        if parsed < 0 or parsed > 100:
            raise ValueError
        return parsed
    except (TypeError, ValueError) as exc:
        raise ValidationError({field_name: 'Enter a numeric score between 0 and 100.'}) from exc


def apply_application_search_filters(applications, query_params, allow_status=True):
    """Apply recruiter-style search, filter, score, and sorting controls to application querysets."""
    search = (query_params.get('search') or '').strip()
    if search:
        applications = applications.filter(
            Q(applicant__full_name__icontains=search)
            | Q(applicant__email__icontains=search)
            | Q(job__title__icontains=search)
            | Q(recruiter_remark__icontains=search)
            | Q(extracted_resume_text__icontains=search)
        )

    if allow_status:
        status_filter = (query_params.get('status') or '').strip()
        if status_filter:
            statuses = [item.strip() for item in status_filter.split(',') if item.strip()]
            invalid_statuses = [item for item in statuses if item not in JobApplication.Status.values]
            if invalid_statuses:
                raise ValidationError({'status': f'Unsupported application status: {", ".join(invalid_statuses)}.'})
            applications = applications.filter(status__in=statuses)

    job_id = (query_params.get('job') or query_params.get('job_id') or '').strip()
    if job_id:
        if not job_id.isdigit():
            raise ValidationError({'job': 'Enter a valid job id.'})
        applications = applications.filter(job_id=job_id)

    min_score = parse_decimal_filter(query_params.get('min_score'), 'min_score')
    max_score = parse_decimal_filter(query_params.get('max_score'), 'max_score')
    if min_score is not None:
        applications = applications.filter(final_score__gte=min_score)
    if max_score is not None:
        applications = applications.filter(final_score__lte=max_score)

    sort_key = (query_params.get('sort') or 'newest').strip()
    ordering = APPLICATION_SORT_OPTIONS.get(sort_key)
    if ordering is None:
        raise ValidationError({'sort': 'Unsupported sort option.'})
    return applications.order_by(*ordering)


def recruiter_job_or_404(user, job_id):
    if user.role != User.Role.RECRUITER:
        raise PermissionDenied('Only recruiters can access candidate ranking and shortlisting APIs.')
    membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
    if not membership:
        raise PermissionDenied('Recruiter must belong to an active organization.')
    return get_object_or_404(
        JobPosting.objects.select_related('organization', 'recruiter'),
        id=job_id,
        recruiter=user,
        organization=membership.organization,
    )


def recruiter_application_or_404(user, application_id):
    if user.role != User.Role.RECRUITER:
        raise PermissionDenied('Only recruiters can manage candidate ranking and shortlisting.')
    return get_object_or_404(visible_applications_for(user), id=application_id)


def resume_application_or_404(user, application_id):
    if user.role in (User.Role.RECRUITER, User.Role.INTERVIEWER):
        return candidate_profile_application_or_404(user, application_id)
    if user.role in (User.Role.APPLICANT, User.Role.HR_HEAD):
        return get_object_or_404(visible_applications_for(user), id=application_id)
    raise PermissionDenied('Your role cannot view application resumes.')


def candidate_profile_application_or_404(user, application_id):
    if user.role == User.Role.RECRUITER:
        return recruiter_application_or_404(user, application_id)
    if user.role == User.Role.INTERVIEWER:
        membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
        if not membership:
            raise PermissionDenied('Interviewer must belong to an active organization.')
        return get_object_or_404(
            JobApplication.objects.select_related(
                'job',
                'job__organization',
                'applicant',
                'applicant__applicant_profile',
                'assigned_interviewer',
                'resume',
            ),
            id=application_id,
            assigned_interviewer=user,
            job__organization=membership.organization,
        )
    raise PermissionDenied('Only recruiters and assigned interviewers can view candidate profiles.')


def active_interviewer_for_organization_or_404(interviewer_id, organization):
    membership = get_object_or_404(
        OrganizationMembership.objects.select_related('user'),
        user_id=interviewer_id,
        user__role=User.Role.INTERVIEWER,
        user__is_active=True,
        organization=organization,
        role=OrganizationMembership.Role.INTERVIEWER,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return membership.user


def create_stage_history(application, from_stage, to_stage, changed_by, note):
    return ApplicationStageHistory.objects.create(
        application=application,
        from_stage=from_stage,
        to_stage=to_stage,
        changed_by=changed_by,
        note=note,
    )


def ensure_application_viewer_role(user):
    if user.role not in (User.Role.APPLICANT, User.Role.RECRUITER, User.Role.HR_HEAD):
        raise PermissionDenied('Your role cannot view job applications.')


class JobApplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can apply for jobs.')
        job = get_object_or_404(
            JobPosting.objects.select_related('organization'),
            id=job_id,
            status=JobPosting.Status.OPEN,
            organization__status=Organization.Status.ACTIVE,
        )
        selected_resume = select_applicant_resume(request.user, request.data.get('resume_id'))
        legacy_resume_file = request.user.applicant_profile.resume_file
        if not selected_resume and not legacy_resume_file:
            raise ValidationError({'resume_file': 'Upload a resume before applying so AI screening can run immediately.'})

        try:
            with transaction.atomic():
                application, created = JobApplication.objects.get_or_create(
                    job=job,
                    applicant=request.user,
                    defaults={'resume': selected_resume},
                )
                if not created:
                    raise ValidationError({'job': 'You have already applied for this job.'})
                application = screen_job_application(application, changed_by=None)
        except ResumeTextExtractionError as exc:
            raise ValidationError({'resume_file': str(exc)}) from exc

        return Response(JobApplicationSerializer(application, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def delete(self, request, job_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can withdraw job applications.')
        application = get_object_or_404(JobApplication, job_id=job_id, applicant=request.user)
        if application.status not in (
            JobApplication.Status.SUBMITTED,
            JobApplication.Status.SCREENED,
            JobApplication.Status.SCREENED_QUALIFIED,
            JobApplication.Status.SCREENED_NOT_QUALIFIED,
        ):
            raise ValidationError({'status': 'Applications can be withdrawn only while submitted or screened.'})
        application.change_status(
            JobApplication.Status.WITHDRAWN,
            changed_by=request.user,
            note='Withdrawn by applicant.',
        )
        return Response(JobApplicationSerializer(application, context={'request': request}).data)


class ApplicationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_application_viewer_role(request.user)
        applications = apply_application_search_filters(
            visible_applications_for(request.user),
            request.query_params,
        )
        return Response(JobApplicationSerializer(applications, many=True, context={'request': request}).data)


class ApplicationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        ensure_application_viewer_role(request.user)
        application = get_object_or_404(visible_applications_for(request.user), id=application_id)
        return Response(JobApplicationSerializer(application, context={'request': request}).data)


class ApplicationStatusHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        ensure_application_viewer_role(request.user)
        application = get_object_or_404(visible_applications_for(request.user), id=application_id)
        history = application.stage_history.select_related('changed_by')
        return Response(ApplicationStageHistorySerializer(history, many=True).data)


class ApplicationScreenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can screen job applications.')

        application = get_object_or_404(visible_applications_for(request.user), id=application_id)
        try:
            resume_file = get_application_resume_file(application)
            if not resume_file:
                raise ValidationError({'resume_file': 'The applicant must upload a resume before screening.'})
            previous_status = application.status
            application = screen_job_application(application, changed_by=request.user)
        except ResumeTextExtractionError as exc:
            raise ValidationError({'resume_file': str(exc)}) from exc

        if previous_status != application.status:
            create_notification(
                application.applicant,
                'application_status_update',
                'Application status updated',
                f'Your application for {application.job.title} is now {application.get_status_display()}.',
                related_entity=application,
            )

        return Response(JobApplicationSerializer(application, context={'request': request}).data)


class RankedCandidatesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = recruiter_job_or_404(request.user, job_id)
        applications = apply_application_search_filters(
            job.applications.filter(status=JobApplication.Status.SCREENED_QUALIFIED).select_related(
                'job',
                'job__organization',
                'applicant',
                'applicant__applicant_profile',
                'assigned_interviewer',
                'resume',
            ),
            request.query_params,
            allow_status=False,
        )
        return Response(JobApplicationSerializer(applications, many=True, context={'request': request}).data)


class CandidateProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        application = candidate_profile_application_or_404(request.user, application_id)
        return Response(CandidateProfileSerializer(application, context={'request': request}).data)


class ApplicationResumeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        application = resume_application_or_404(request.user, application_id)
        resume_file = get_application_resume_file(application)
        if not resume_file:
            return Response({'detail': 'Resume file not found.'}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(resume_file.open('rb'), as_attachment=False, filename=resume_file.name.split('/')[-1])


class ApplicationShortlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, application_id):
        application = recruiter_application_or_404(request.user, application_id)
        serializer = ApplicationShortlistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interviewer = active_interviewer_for_organization_or_404(
            serializer.validated_data['interviewer_id'],
            application.job.organization,
        )
        previous_status = application.status
        application.assigned_interviewer = interviewer
        remark = serializer.validated_data.get('remark', '')
        if remark:
            application.recruiter_remark = remark
        application.status = JobApplication.Status.SHORTLISTED
        application.save(update_fields=['assigned_interviewer', 'recruiter_remark', 'status', 'updated_at'])
        create_stage_history(
            application,
            previous_status,
            JobApplication.Status.SHORTLISTED,
            request.user,
            f'Shortlisted and assigned to interviewer {interviewer.full_name}.',
        )
        create_notification(
            application.applicant,
            'application_status_update',
            'Application status updated',
            f'Your application for {application.job.title} has been shortlisted.',
            related_entity=application,
        )
        create_notification(
            interviewer,
            'interview_assignment',
            'Candidate assigned',
            f'{application.applicant.full_name} was shortlisted and assigned to you for {application.job.title}.',
            related_entity=application,
        )
        return Response(JobApplicationSerializer(application, context={'request': request}).data)


class ApplicationRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, application_id):
        application = recruiter_application_or_404(request.user, application_id)
        serializer = ApplicationRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        previous_status = application.status
        reason = serializer.validated_data.get('reason', '')
        remark = serializer.validated_data.get('remark', '')
        application.status = JobApplication.Status.REJECTED
        application.recruiter_remark = remark or reason
        application.save(update_fields=['status', 'recruiter_remark', 'updated_at'])
        create_stage_history(
            application,
            previous_status,
            JobApplication.Status.REJECTED,
            request.user,
            reason or remark,
        )
        candidate_message = remark or reason or f'Your application for {application.job.title} was not selected.'
        create_notification(
            application.applicant,
            'application_status_update',
            'Application status updated',
            candidate_message,
            related_entity=application,
        )
        return Response(JobApplicationSerializer(application, context={'request': request}).data)


class ApplicationRemarkAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, application_id):
        application = recruiter_application_or_404(request.user, application_id)
        serializer = ApplicationRemarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application.recruiter_remark = serializer.validated_data['remark']
        application.save(update_fields=['recruiter_remark', 'updated_at'])
        create_stage_history(
            application,
            application.status,
            application.status,
            request.user,
            'Recruiter remark updated.',
        )
        return Response(JobApplicationSerializer(application, context={'request': request}).data)
