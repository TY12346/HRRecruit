"""Role-protected and organization-isolated interview management APIs."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.notifications.services import create_notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import CalendarEvent, Interview, InterviewInvitation
from .serializers import (
    AssignInterviewerSerializer,
    DeclineInterviewInvitationSerializer,
    InterviewInvitationSerializer,
    InterviewSerializer,
    SendInterviewInvitationSerializer,
)
from .services import build_calendar_link


def get_active_membership(user, role):
    return OrganizationMembership.objects.filter(
        user=user,
        role=role,
        status=OrganizationMembership.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    ).select_related('organization').first()


def base_interview_queryset():
    return Interview.objects.select_related(
        'application',
        'application__job',
        'application__job__organization',
        'application__applicant',
        'application__applicant__applicant_profile',
        'organization',
        'recruiter',
        'interviewer',
    ).prefetch_related('invitations', 'status_history', 'calendar_events')


def visible_interviews_for(user):
    interviews = base_interview_queryset()
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        if membership:
            return interviews.filter(organization=membership.organization, recruiter=user)
    elif user.role == User.Role.INTERVIEWER:
        membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
        if membership:
            return interviews.filter(organization=membership.organization, interviewer=user)
    elif user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
        if membership:
            return interviews.filter(organization=membership.organization)
    elif user.role == User.Role.APPLICANT:
        return interviews.filter(application__applicant=user)
    return interviews.none()


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


def recruiter_application_or_404(user, application_id):
    if user.role != User.Role.RECRUITER:
        raise PermissionDenied('Only recruiters can assign interviewers.')
    membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
    if not membership:
        raise PermissionDenied('Recruiter must belong to an active organization.')
    return get_object_or_404(
        JobApplication.objects.select_related('job', 'job__organization', 'applicant', 'assigned_interviewer'),
        id=application_id,
        job__organization=membership.organization,
        job__recruiter=user,
    )


def change_application_status(application, new_status, changed_by, note):
    previous_status = application.status
    if previous_status == new_status:
        return None
    application.status = new_status
    application.save(update_fields=['status', 'updated_at'])
    return ApplicationStageHistory.objects.create(
        application=application,
        from_stage=previous_status,
        to_stage=new_status,
        changed_by=changed_by,
        note=note,
    )


class InterviewListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interviews = visible_interviews_for(request.user)
        return Response(InterviewSerializer(interviews, many=True, context={'request': request}).data)


class AssignedInterviewListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can view assigned interviews.')
        interviews = visible_interviews_for(request.user)
        return Response(InterviewSerializer(interviews, many=True, context={'request': request}).data)


class InterviewDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, interview_id):
        interview = get_object_or_404(visible_interviews_for(request.user), id=interview_id)
        return Response(InterviewSerializer(interview, context={'request': request}).data)


class AssignInterviewerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, application_id):
        application = recruiter_application_or_404(request.user, application_id)
        if application.status in (JobApplication.Status.WITHDRAWN, JobApplication.Status.REJECTED):
            raise ValidationError({'status': 'Withdrawn or rejected applications cannot be assigned for interview.'})

        serializer = AssignInterviewerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interviewer = active_interviewer_for_organization_or_404(
            serializer.validated_data['interviewer_id'],
            application.job.organization,
        )

        application.assigned_interviewer = interviewer
        update_fields = ['assigned_interviewer', 'updated_at']
        if application.status != JobApplication.Status.SHORTLISTED:
            previous_status = application.status
            application.status = JobApplication.Status.SHORTLISTED
            update_fields.append('status')
        else:
            previous_status = application.status
        application.save(update_fields=update_fields)
        if previous_status != application.status:
            ApplicationStageHistory.objects.create(
                application=application,
                from_stage=previous_status,
                to_stage=application.status,
                changed_by=request.user,
                note='Shortlisted during interviewer assignment.',
            )

        interview, created = Interview.objects.get_or_create(
            application=application,
            defaults={
                'organization': application.job.organization,
                'recruiter': request.user,
                'interviewer': interviewer,
                'status': Interview.Status.ASSIGNED,
            },
        )
        previous_interviewer = interview.interviewer
        if not created:
            interview.organization = application.job.organization
            interview.recruiter = request.user
            interview.interviewer = interviewer
            interview.save(update_fields=['organization', 'recruiter', 'interviewer', 'updated_at'])
        if created:
            interview.change_status(Interview.Status.ASSIGNED, changed_by=request.user, note='Interview assigned.')
        elif previous_interviewer != interviewer:
            # Keep status unchanged but record assignment notes as a history row for traceability.
            interview.status_history.create(
                from_status=interview.status,
                to_status=interview.status,
                changed_by=request.user,
                note=f'Interviewer reassigned to {interviewer.full_name}.',
            )

        create_notification(
            interviewer,
            'interview_assignment',
            'New interview assignment',
            f'You were assigned to interview {application.applicant.full_name} for {application.job.title}.',
            related_entity=interview,
        )
        return Response(InterviewSerializer(interview, context={'request': request}).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class SendInterviewInvitationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, interview_id):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only assigned interviewers can send interview invitations.')
        interview = get_object_or_404(visible_interviews_for(request.user), id=interview_id)
        serializer = SendInterviewInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation = InterviewInvitation.objects.create(interview=interview, **serializer.validated_data)
        interview.mode = invitation.mode
        interview.meeting_link = invitation.meeting_link
        interview.location = invitation.location
        interview.save(update_fields=['mode', 'meeting_link', 'location', 'updated_at'])
        interview.change_status(
            Interview.Status.INVITATION_SENT,
            changed_by=request.user,
            note=f'Invitation sent for {invitation.proposed_datetime.isoformat()}.',
        )
        change_application_status(
            interview.application,
            JobApplication.Status.INTERVIEW_INVITED,
            request.user,
            'Interview invitation sent.',
        )
        create_notification(
            interview.application.applicant,
            'interview_invitation',
            'Interview invitation received',
            f'You have a new interview invitation for {interview.application.job.title}.',
            related_entity=invitation,
        )
        return Response(InterviewInvitationSerializer(invitation, context={'request': request}).data, status=status.HTTP_201_CREATED)


class InterviewInvitationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == User.Role.APPLICANT:
            invitations = InterviewInvitation.objects.filter(
                interview__application__applicant=request.user,
            )
        elif request.user.role == User.Role.INTERVIEWER:
            invitations = InterviewInvitation.objects.filter(
                interview__in=visible_interviews_for(request.user),
            )
        else:
            raise PermissionDenied('Only applicants and interviewers can view interview invitations here.')
        invitations = invitations.select_related(
            'interview',
            'interview__application',
            'interview__application__job',
            'interview__application__job__organization',
            'interview__application__applicant',
            'interview__application__applicant__applicant_profile',
            'interview__interviewer',
        )
        return Response(InterviewInvitationSerializer(invitations, many=True, context={'request': request}).data)


class AcceptInterviewInvitationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, invitation_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can accept interview invitations.')
        invitation = get_object_or_404(
            InterviewInvitation.objects.select_related('interview', 'interview__application', 'interview__application__job', 'interview__interviewer'),
            id=invitation_id,
            interview__application__applicant=request.user,
        )
        if invitation.status != InterviewInvitation.Status.PENDING:
            raise ValidationError({'status': 'Only pending invitations can be accepted.'})

        invitation.status = InterviewInvitation.Status.ACCEPTED
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=['status', 'responded_at'])

        interview = invitation.interview
        interview.scheduled_datetime = invitation.proposed_datetime
        interview.mode = invitation.mode
        interview.meeting_link = invitation.meeting_link
        interview.location = invitation.location
        interview.save(update_fields=['scheduled_datetime', 'mode', 'meeting_link', 'location', 'updated_at'])
        interview.change_status(Interview.Status.SCHEDULED, changed_by=request.user, note='Invitation accepted by applicant.')
        change_application_status(
            interview.application,
            JobApplication.Status.INTERVIEW_ACCEPTED,
            request.user,
            'Interview invitation accepted.',
        )
        calendar_link = build_calendar_link(interview)
        CalendarEvent.objects.update_or_create(
            interview=interview,
            provider='local',
            defaults={
                'calendar_link': calendar_link,
                'sync_status': CalendarEvent.SyncStatus.NOT_SYNCED,
            },
        )
        create_notification(
            interview.interviewer,
            'invitation_response',
            'Interview invitation accepted',
            f'{request.user.full_name} accepted the interview invitation.',
            related_entity=invitation,
        )
        return Response(InterviewInvitationSerializer(invitation, context={'request': request}).data)


class DeclineInterviewInvitationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, invitation_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can decline interview invitations.')
        invitation = get_object_or_404(
            InterviewInvitation.objects.select_related('interview', 'interview__application', 'interview__application__job', 'interview__interviewer'),
            id=invitation_id,
            interview__application__applicant=request.user,
        )
        if invitation.status != InterviewInvitation.Status.PENDING:
            raise ValidationError({'status': 'Only pending invitations can be declined.'})
        serializer = DeclineInterviewInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation.status = InterviewInvitation.Status.DECLINED
        invitation.decline_reason = serializer.validated_data['decline_reason']
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=['status', 'decline_reason', 'responded_at'])

        interview = invitation.interview
        interview.change_status(
            Interview.Status.DECLINED,
            changed_by=request.user,
            note=f'Invitation declined: {invitation.decline_reason}',
        )
        change_application_status(
            interview.application,
            JobApplication.Status.INTERVIEW_DECLINED,
            request.user,
            invitation.decline_reason,
        )
        create_notification(
            interview.interviewer,
            'invitation_response',
            'Interview invitation declined',
            f'{request.user.full_name} declined the interview invitation.',
            related_entity=invitation,
        )
        return Response(InterviewInvitationSerializer(invitation, context={'request': request}).data)
