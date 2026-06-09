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
from apps.notifications.email_service import send_job_offer_email
from apps.notifications.services import create_bulk_notifications, create_notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User
from .models import HiringDecision, JobOffer
from .serializers import (
    HiringDecisionSerializer,
    HiringDecisionSubmitSerializer,
    HRDecisionReviewSerializer,
    JobOfferCreateSerializer,
    JobOfferDeclineSerializer,
    JobOfferSerializer,
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
        return offers.filter(application__applicant=user)
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
        raise PermissionDenied('An active HR head organization membership is required.')
    decision = get_object_or_404(
        HiringDecision.objects.select_for_update(),
        id=decision_id,
        status=HiringDecision.Status.PENDING_HR_APPROVAL,
    )
    if decision.application.job.organization_id != membership.organization_id:
        raise Http404('Hiring decision not found.')
    return decision


def applicant_offer_for_update_or_404(user, offer_id):
    offer = get_object_or_404(JobOffer.objects.select_for_update(), id=offer_id)
    if offer.application.applicant_id != user.id:
        raise Http404('Job offer not found.')
    return offer


def change_application_status(application, new_status, changed_by, note):
    return application.change_status(new_status, changed_by=changed_by, note=note)


class HiringDecisionSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, application_id):
        application = recruiter_application_or_404(request.user, application_id)
        if application.status in (
            JobApplication.Status.WITHDRAWN,
            JobApplication.Status.REJECTED,
            JobApplication.Status.OFFER_SENT,
            JobApplication.Status.OFFER_ACCEPTED,
            JobApplication.Status.OFFER_DECLINED,
            JobApplication.Status.HIRED,
        ):
            raise ValidationError({'status': 'This application cannot be submitted for a hiring decision.'})
        if HiringDecision.objects.filter(
            application=application,
            status=HiringDecision.Status.PENDING_HR_APPROVAL,
        ).exists():
            raise ValidationError({'application': 'This application already has a pending hiring decision.'})
        if HiringDecision.objects.filter(
            application=application,
            decision=HiringDecision.Decision.HIRE,
            status=HiringDecision.Status.APPROVED,
        ).exists():
            raise ValidationError({'application': 'This application already has an approved hire decision.'})

        serializer = HiringDecisionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = HiringDecision.objects.create(
            application=application,
            recruiter=request.user,
            decision=serializer.validated_data['decision'],
            recruiter_justification=serializer.validated_data['justification'],
        )
        change_application_status(
            application,
            JobApplication.Status.DECISION_PENDING,
            request.user,
            f'Recruiter submitted {decision.decision} decision for HR approval.',
        )
        hr_heads = list(organization_hr_heads(application.job.organization))
        create_bulk_notifications(
            hr_heads,
            'hiring_decision_submitted',
            'Hiring decision pending approval',
            f'{request.user.full_name} submitted a {decision.decision} decision for {application.applicant.full_name}.',
            related_entity=decision,
        )
        return Response(HiringDecisionSerializer(decision, context={'request': request}).data, status=status.HTTP_201_CREATED)


class PendingHiringDecisionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.HR_HEAD:
            raise PermissionDenied('Only HR heads can view pending hiring decisions.')
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
            raise PermissionDenied('Only HR heads can approve hiring decisions.')
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
            new_status = JobApplication.Status.HR_APPROVED
            note = f'HR approved hire decision: {decision.hr_head_justification}'
        else:
            new_status = JobApplication.Status.REJECTED
            note = f'HR approved reject decision: {decision.hr_head_justification}'
        change_application_status(application, new_status, request.user, note)
        create_notification(
            decision.recruiter,
            'hiring_decision_reviewed',
            'Hiring decision approved',
            f'HR approved your {decision.decision} decision for {application.applicant.full_name}.',
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
            raise PermissionDenied('Only HR heads can reject hiring decisions.')
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
            JobApplication.Status.HR_REJECTED,
            request.user,
            f'HR rejected {decision.decision} decision: {decision.hr_head_justification}',
        )
        create_notification(
            decision.recruiter,
            'hiring_decision_reviewed',
            'Hiring decision rejected by HR',
            f'HR rejected your {decision.decision} decision for {application.applicant.full_name}.',
            related_entity=decision,
        )
        return Response(HiringDecisionSerializer(decision, context={'request': request}).data)


class JobOfferCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request, application_id):
        application = recruiter_application_or_404(request.user, application_id)
        approved_hire_exists = HiringDecision.objects.filter(
            application=application,
            recruiter=request.user,
            decision=HiringDecision.Decision.HIRE,
            status=HiringDecision.Status.APPROVED,
        ).exists()
        if not approved_hire_exists or application.status != JobApplication.Status.HR_APPROVED:
            raise ValidationError({'application': 'A job offer can only be sent after HR approves a hire decision.'})
        if JobOffer.objects.filter(application=application, offer_status=JobOffer.OfferStatus.SENT).exists():
            raise ValidationError({'application': 'This application already has a sent job offer.'})

        serializer = JobOfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer = JobOffer.objects.create(application=application, **serializer.validated_data)
        change_application_status(application, JobApplication.Status.OFFER_SENT, request.user, 'Recruiter sent job offer.')
        create_notification(
            application.applicant,
            'job_offer_sent',
            'Job offer received',
            f'You received a job offer for {application.job.title}.',
            related_entity=offer,
        )
        create_bulk_notifications(
            list(organization_hr_heads(application.job.organization)),
            'job_offer_sent',
            'Job offer sent',
            f'{request.user.full_name} sent a job offer to {application.applicant.full_name}.',
            related_entity=offer,
        )
        send_job_offer_email(offer)
        return Response(JobOfferSerializer(offer, context={'request': request}).data, status=status.HTTP_201_CREATED)


class JobOfferListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = visible_offers_for(request.user)
        return Response(JobOfferSerializer(offers, many=True, context={'request': request}).data)


class JobOfferAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, offer_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can accept job offers.')
        offer = applicant_offer_for_update_or_404(request.user, offer_id)
        if offer.offer_status != JobOffer.OfferStatus.SENT:
            raise ValidationError({'offer_status': 'Only sent job offers can be accepted.'})
        if offer.respond_deadline < timezone.now():
            offer.offer_status = JobOffer.OfferStatus.EXPIRED
            offer.save(update_fields=['offer_status'])
            raise ValidationError({'respond_deadline': 'This job offer has expired.'})

        offer.offer_status = JobOffer.OfferStatus.ACCEPTED
        offer.responded_at = timezone.now()
        offer.save(update_fields=['offer_status', 'responded_at'])
        application = offer.application
        change_application_status(application, JobApplication.Status.OFFER_ACCEPTED, request.user, 'Applicant accepted job offer.')
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
        if offer.offer_status != JobOffer.OfferStatus.SENT:
            raise ValidationError({'offer_status': 'Only sent job offers can be declined.'})
        serializer = JobOfferDeclineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        offer.offer_status = JobOffer.OfferStatus.DECLINED
        offer.responded_at = timezone.now()
        offer.save(update_fields=['offer_status', 'responded_at'])
        application = offer.application
        decline_note = serializer.validated_data.get('reason') or 'Applicant declined job offer.'
        change_application_status(application, JobApplication.Status.OFFER_DECLINED, request.user, decline_note)
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
