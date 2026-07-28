"""Role-protected and organization-isolated interview management APIs."""

import logging
from collections import defaultdict
from datetime import datetime

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.notifications.services import create_notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import Interview, InterviewSchedulingRequest, InterviewerAvailabilityPattern, InterviewerUnavailableDate, InterviewerAvailabilitySlot
from .serializers import (
    AssignInterviewerSerializer,
    BookSchedulingRequestSerializer,
    CreateSchedulingRequestSerializer,
    GoogleCalendarConnectSerializer,
    GoogleCalendarOAuthCallbackSerializer,
    InterviewSchedulingRequestSerializer,
    InterviewSerializer,
    InterviewerAvailabilityPatternSerializer,
    InterviewerUnavailableDateSerializer,
    InterviewerAvailabilitySlotSerializer,
)
from .calendar_service import (
    GoogleCalendarConfigurationError,
    GoogleCalendarSyncError,
    build_google_calendar_authorization_url,
    disconnect_google_calendar,
    google_calendar_status_for_user,
    store_google_calendar_credentials,
    sync_calendar_event_for_interview,
    sync_existing_google_events_for_user,
)
from .slot_generation import generate_common_available_slots


logger = logging.getLogger(__name__)



def ensure_calendar_oauth_role(user):
    if user.role not in (User.Role.RECRUITER, User.Role.INTERVIEWER):
        raise PermissionDenied('Only recruiters and interviewers can connect Google Calendar.')


class GoogleCalendarStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_calendar_oauth_role(request.user)
        return Response(google_calendar_status_for_user(request.user))


class GoogleCalendarConnectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_calendar_oauth_role(request.user)
        serializer = GoogleCalendarConnectSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            authorization_url = build_google_calendar_authorization_url(
                request.user,
                next_url=serializer.validated_data.get('next', ''),
            )
        except GoogleCalendarConfigurationError as exc:
            raise ValidationError({'google_calendar': str(exc)}) from exc
        status_payload = google_calendar_status_for_user(request.user)
        status_payload['authorization_url'] = authorization_url
        return Response(status_payload)


class GoogleCalendarOAuthCallbackAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ensure_calendar_oauth_role(request.user)
        serializer = GoogleCalendarOAuthCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            credential = store_google_calendar_credentials(
                request.user,
                code=serializer.validated_data['code'],
                state=serializer.validated_data['state'],
            )
            sync_result = sync_existing_google_events_for_user(request.user)
        except GoogleCalendarConfigurationError as exc:
            raise ValidationError({'google_calendar': str(exc)}) from exc
        except GoogleCalendarSyncError as exc:
            raise ValidationError({'google_calendar': str(exc)}) from exc
        return Response({
            'connected': True,
            'connected_email': credential.google_account_email,
            'oauth_ready': True,
            'synced_interviews': sync_result['synced'],
            'failed_interview_syncs': sync_result['failed'],
        })


class GoogleCalendarDisconnectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        ensure_calendar_oauth_role(request.user)
        disconnected = disconnect_google_calendar(request.user)
        return Response({'connected': False, 'disconnected': disconnected})


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
        'scheduling_request',
    ).prefetch_related('application__job__interview_evaluation_form__criteria', 'status_history', 'calendar_events', 'panel_interviewers')


def visible_interviews_for(user):
    interviews = base_interview_queryset()
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        if membership:
            return interviews.filter(
                organization=membership.organization,
                application__job__organization=membership.organization,
                application__job__recruiter=user,
                recruiter=user,
            )
    elif user.role == User.Role.INTERVIEWER:
        membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
        if membership:
            return interviews.filter(Q(interviewer=user) | Q(panel_interviewers=user), organization=membership.organization).distinct()
    elif user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
        if membership:
            return interviews.filter(organization=membership.organization)
    elif user.role == User.Role.APPLICANT:
        return interviews.filter(application__applicant=user)
    return interviews.none()



def visible_scheduling_requests_for(user):
    requests = InterviewSchedulingRequest.objects.select_related(
        'application',
        'application__job',
        'application__job__organization',
        'application__applicant',
        'application__applicant__applicant_profile',
        'organization',
        'recruiter',
        'interviewer',
        'selected_slot',
        'interview',
    ).prefetch_related('panel_interviewers')
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        if membership:
            return requests.filter(organization=membership.organization, recruiter=user)
    if user.role == User.Role.INTERVIEWER:
        membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
        if membership:
            return requests.filter(Q(interviewer=user) | Q(panel_interviewers=user), organization=membership.organization).distinct()
    if user.role == User.Role.APPLICANT:
        return requests.filter(application__applicant=user, invitation_sent_at__isnull=False)
    if user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
        if membership:
            return requests.filter(organization=membership.organization)
    return requests.none()


def bookable_scheduling_requests_for_applicant(applicant):
    """Return scheduling requests for booking without nullable joins.

    PostgreSQL rejects SELECT ... FOR UPDATE when the query includes nullable
    outer joins, so the booking lock queryset intentionally avoids selected_slot
    and interview select_related joins.
    """
    return InterviewSchedulingRequest.objects.select_related(
        'application',
        'application__job',
        'application__job__organization',
        'application__applicant',
        'organization',
        'recruiter',
        'interviewer',
    ).prefetch_related('panel_interviewers').filter(
        application__applicant=applicant,
        invitation_sent_at__isnull=False,
    )


def available_slots_for_interviewer(user):
    membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
    if not membership:
        raise PermissionDenied('Interviewer must belong to an active organization.')
    return InterviewerAvailabilitySlot.objects.filter(organization=membership.organization, interviewer=user)



def pending_scheduling_request_for_applicant_application_or_404(applicant, application_id):
    scheduling_request = (
        bookable_scheduling_requests_for_applicant(applicant)
        .filter(
            application_id=application_id,
            status=InterviewSchedulingRequest.Status.PENDING,
        )
        .order_by('-created_at', '-id')
        .first()
    )
    if not scheduling_request:
        raise Http404
    return scheduling_request


def panel_interviewers_for_scheduling_request(scheduling_request):
    return list(scheduling_request.panel_interviewers.all()) or [scheduling_request.interviewer]


def selectable_slots_for_scheduling_request(scheduling_request, selected_date=None):
    panel = panel_interviewers_for_scheduling_request(scheduling_request)
    generated_slots = generate_common_available_slots(panel, scheduling_request.organization)
    if selected_date:
        generated_slots = [slot for slot in generated_slots if slot.date == selected_date]
    legacy_slots = []
    if len(panel) == 1:
        legacy_slots = InterviewerAvailabilitySlot.objects.filter(
            organization=scheduling_request.organization,
            interviewer=scheduling_request.interviewer,
            status=InterviewerAvailabilitySlot.Status.AVAILABLE,
            start_datetime__gt=timezone.now(),
        ).order_by('start_datetime')
        if selected_date:
            legacy_slots = [slot for slot in legacy_slots if timezone.localdate(slot.start_datetime) == selected_date]
    return generated_slots, legacy_slots


def panel_interviewer_names(panel):
    return [interviewer.full_name for interviewer in panel if interviewer]


def scheduling_request_has_common_slot(scheduling_request):
    generated_slots, legacy_slots = selectable_slots_for_scheduling_request(scheduling_request)
    return bool(generated_slots or legacy_slots)


def send_newly_available_scheduling_invitations(interviewer, organization):
    """Invite applicants once a pending panel obtains at least one common slot."""
    pending_requests = InterviewSchedulingRequest.objects.filter(
        Q(interviewer=interviewer) | Q(panel_interviewers=interviewer),
        organization=organization,
        status=InterviewSchedulingRequest.Status.PENDING,
        invitation_sent_at__isnull=True,
    ).select_related('application__applicant', 'application__job').prefetch_related('panel_interviewers').distinct()
    for scheduling_request in pending_requests:
        if not scheduling_request_has_common_slot(scheduling_request):
            continue
        sent_at = timezone.now()
        updated = InterviewSchedulingRequest.objects.filter(
            id=scheduling_request.id,
            invitation_sent_at__isnull=True,
        ).update(invitation_sent_at=sent_at, updated_at=sent_at)
        if updated:
            create_notification(
                scheduling_request.application.applicant,
                'interview_self_scheduling',
                f'Choose an interview time for {scheduling_request.application.job.title}',
                f'Please choose an interview slot for {scheduling_request.application.job.title}.',
                related_entity=scheduling_request,
            )


def active_interview_conflict_exists(panel, organization, selected_date, start_time, end_time):
    """Return whether any panel member is already booked for the selected time.

    Keep the primary-interviewer and panel-interviewer checks separate to avoid
    outer-join SQL shapes during applicant self-booking.
    """
    base_filters = {
        'organization': organization,
        'interview_date': selected_date,
        'start_time': start_time,
        'end_time': end_time,
        'status__in': [Interview.Status.INVITED, Interview.Status.SCHEDULED],
    }
    primary_conflict = Interview.objects.filter(
        interviewer__in=panel,
        **base_filters,
    ).exists()
    if primary_conflict:
        return True
    return Interview.objects.filter(
        panel_interviewers__in=panel,
        **base_filters,
    ).distinct().exists()


def get_or_create_application_interview(application, defaults):
    """Return one interview for an application without assuming historical uniqueness.

    Older flows can leave more than one Interview row for an application. Django's
    get_or_create(application=...) raises MultipleObjectsReturned in that state,
    which surfaces to Flutter as a generic 500 during slot booking. Prefer the
    newest row and only create one when none exists.
    """
    interview = Interview.objects.filter(application=application).order_by('-id').first()
    if interview:
        return interview, False
    return Interview.objects.create(application=application, **defaults), True


def serialize_generated_slot_for_selection(slot, interviewer, panel=None):
    return {
        'slot_id': slot.id,
        'id': slot.id,
        'pattern_id': slot.pattern_id,
        'date': slot.date,
        'interview_date': slot.date,
        'start_time': slot.start_time,
        'end_time': slot.end_time,
        'start_datetime': slot.start_datetime,
        'end_datetime': slot.end_datetime,
        'mode': slot.mode,
        'meeting_link': slot.meeting_link,
        'location': slot.location,
        'interviewer_names': panel_interviewer_names(panel or ([interviewer] if interviewer else [])),
        'status': slot.status,
    }


def serialize_legacy_slot_for_selection(slot, interviewer, panel=None):
    return {
        'slot_id': slot.id,
        'id': slot.id,
        'pattern_id': None,
        'date': timezone.localdate(slot.start_datetime),
        'interview_date': timezone.localdate(slot.start_datetime),
        'start_time': timezone.localtime(slot.start_datetime).time().replace(microsecond=0),
        'end_time': timezone.localtime(slot.end_datetime).time().replace(microsecond=0),
        'start_datetime': slot.start_datetime,
        'end_datetime': slot.end_datetime,
        'mode': Interview.Mode.ONLINE,
        'meeting_link': '',
        'location': '',
        'interviewer_names': panel_interviewer_names(panel or ([interviewer] if interviewer else [])),
        'status': slot.status,
    }

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


def create_interview_booking_side_effects(scheduling_request, interview, applicant):
    """Create booking notifications after an applicant selects a slot."""
    notification_payloads = [
        (
            scheduling_request.recruiter,
            f'{applicant.full_name} selected an interview slot for {interview.application.job.title}',
            f'{applicant.full_name} selected an interview slot for {scheduling_request.application.job.title}.',
        ),
        (
            scheduling_request.interviewer,
            f'{applicant.full_name} selected an interview slot for {interview.application.job.title}',
            f'{applicant.full_name} selected your available interview slot.',
        ),
    ]
    for panel_interviewer in scheduling_request.panel_interviewers.exclude(id=scheduling_request.interviewer_id):
        notification_payloads.append((
            panel_interviewer,
            f'{applicant.full_name} selected an interview slot for {interview.application.job.title}',
            f'{applicant.full_name} selected a panel interview slot.',
        ))
    for recipient, title, message in notification_payloads:
        try:
            create_notification(
                recipient,
                'interview_self_scheduled',
                title,
                message,
                related_entity=interview,
            )
        except Exception:
            logger.exception(
                'Failed to create booking notification for interview %s and recipient %s.',
                interview.id,
                getattr(recipient, 'id', None),
            )



def availability_patterns_for_interviewer(user):
    membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
    if not membership:
        raise PermissionDenied('Interviewer must belong to an active organization.')
    return InterviewerAvailabilityPattern.objects.filter(organization=membership.organization, interviewer=user)


def unavailable_dates_for_interviewer(user):
    membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
    if not membership:
        raise PermissionDenied('Interviewer must belong to an active organization.')
    return InterviewerUnavailableDate.objects.filter(organization=membership.organization, interviewer=user)


class InterviewerAvailabilityPatternListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage weekly availability.')
        return Response(InterviewerAvailabilityPatternSerializer(availability_patterns_for_interviewer(request.user), many=True).data)

    def post(self, request):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage weekly availability.')
        membership = get_active_membership(request.user, OrganizationMembership.Role.INTERVIEWER)
        if not membership:
            raise PermissionDenied('Interviewer must belong to an active organization.')
        serializer = InterviewerAvailabilityPatternSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pattern = InterviewerAvailabilityPattern.objects.create(organization=membership.organization, interviewer=request.user, **serializer.validated_data)
        send_newly_available_scheduling_invitations(request.user, membership.organization)
        return Response(InterviewerAvailabilityPatternSerializer(pattern).data, status=status.HTTP_201_CREATED)


class InterviewerAvailabilityPatternDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pattern_id):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage weekly availability.')
        pattern = get_object_or_404(availability_patterns_for_interviewer(request.user), id=pattern_id)
        serializer = InterviewerAvailabilityPatternSerializer(pattern, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pattern_id):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage weekly availability.')
        pattern = get_object_or_404(availability_patterns_for_interviewer(request.user), id=pattern_id)
        pattern.is_active = False
        pattern.save(update_fields=['is_active', 'updated_at'])
        return Response(InterviewerAvailabilityPatternSerializer(pattern).data)


class InterviewerUnavailableDateListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage unavailable dates.')
        return Response(InterviewerUnavailableDateSerializer(unavailable_dates_for_interviewer(request.user), many=True).data)

    def post(self, request):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage unavailable dates.')
        membership = get_active_membership(request.user, OrganizationMembership.Role.INTERVIEWER)
        if not membership:
            raise PermissionDenied('Interviewer must belong to an active organization.')
        serializer = InterviewerUnavailableDateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            unavailable = InterviewerUnavailableDate.objects.create(organization=membership.organization, interviewer=request.user, **serializer.validated_data)
        except IntegrityError as exc:
            raise ValidationError({'date': 'This unavailable date already exists.'}) from exc
        return Response(InterviewerUnavailableDateSerializer(unavailable).data, status=status.HTTP_201_CREATED)


class InterviewerUnavailableDateDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, unavailable_date_id):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage unavailable dates.')
        unavailable = get_object_or_404(unavailable_dates_for_interviewer(request.user), id=unavailable_date_id)
        unavailable.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class InterviewerAvailabilitySlotListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage availability slots.')
        slots = available_slots_for_interviewer(request.user)
        return Response(InterviewerAvailabilitySlotSerializer(slots, many=True, context={'request': request}).data)

    def post(self, request):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can manage availability slots.')
        membership = get_active_membership(request.user, OrganizationMembership.Role.INTERVIEWER)
        if not membership:
            raise PermissionDenied('Interviewer must belong to an active organization.')
        serializer = InterviewerAvailabilitySlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            slot = InterviewerAvailabilitySlot.objects.create(
                organization=membership.organization,
                interviewer=request.user,
                **serializer.validated_data,
            )
        except IntegrityError as exc:
            raise ValidationError({'start_datetime': 'This availability slot could not be saved. Please check for duplicate or invalid times.'}) from exc
        send_newly_available_scheduling_invitations(request.user, membership.organization)
        return Response(InterviewerAvailabilitySlotSerializer(slot, context={'request': request}).data, status=status.HTTP_201_CREATED)


class InterviewerAvailabilitySlotDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, slot_id):
        if request.user.role != User.Role.INTERVIEWER:
            raise PermissionDenied('Only interviewers can cancel availability slots.')
        slot = get_object_or_404(available_slots_for_interviewer(request.user), id=slot_id)
        if slot.status == InterviewerAvailabilitySlot.Status.BOOKED:
            raise ValidationError({'status': 'Booked availability slots cannot be cancelled.'})
        slot.status = InterviewerAvailabilitySlot.Status.CANCELLED
        slot.save(update_fields=['status', 'updated_at'])
        return Response(InterviewerAvailabilitySlotSerializer(slot, context={'request': request}).data)


class CreateSchedulingRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, application_id):
        application = recruiter_application_or_404(request.user, application_id)
        if application.status in (JobApplication.Status.REJECTED, JobApplication.Status.REJECTED):
            raise ValidationError({'status': 'Withdrawn or rejected applications cannot be scheduled for interview.'})
        serializer = CreateSchedulingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        panel_interviewers = [
            active_interviewer_for_organization_or_404(interviewer_id, application.job.organization)
            for interviewer_id in serializer.validated_data['interviewer_ids']
        ]
        interviewer = panel_interviewers[0]

        application.assigned_interviewer = interviewer
        if application.status != JobApplication.Status.UNDER_REVIEW:
            previous_status = application.status
            application.status = JobApplication.Status.UNDER_REVIEW
            application.save(update_fields=['assigned_interviewer', 'status', 'updated_at'])
            ApplicationStageHistory.objects.create(
                application=application,
                from_stage=previous_status,
                to_stage=application.status,
                changed_by=request.user,
                note='Shortlisted during interview scheduling request.',
            )
        else:
            application.save(update_fields=['assigned_interviewer', 'updated_at'])

        interview, interview_created = get_or_create_application_interview(
            application,
            {
                'organization': application.job.organization,
                'recruiter': request.user,
                'interviewer': interviewer,
                'status': Interview.Status.INVITED,
                'scheduling_method': Interview.SchedulingMethod.SELF_SCHEDULED,
            },
        )
        previous_interviewer = interview.interviewer
        if not interview_created:
            interview.organization = application.job.organization
            interview.recruiter = request.user
            interview.interviewer = interviewer
            interview.scheduling_method = Interview.SchedulingMethod.SELF_SCHEDULED
            interview.save(update_fields=['organization', 'recruiter', 'interviewer', 'scheduling_method', 'updated_at'])
        interview.panel_interviewers.set(panel_interviewers)
        if interview_created:
            interview.status_history.create(
                from_status=Interview.Status.INVITED,
                to_status=Interview.Status.INVITED,
                changed_by=request.user,
                note='Interview assigned through self-scheduling request.',
            )
        elif previous_interviewer != interviewer:
            interview.status_history.create(
                from_status=interview.status,
                to_status=interview.status,
                changed_by=request.user,
                note=f'Interviewer reassigned to {interviewer.full_name} through self-scheduling request.',
            )

        scheduling_request = InterviewSchedulingRequest.objects.create(
            application=application,
            organization=application.job.organization,
            recruiter=request.user,
            interviewer=interviewer,
            interview=interview,
            remark=serializer.validated_data.get('remark', ''),
            expires_at=serializer.validated_data.get('expires_at'),
        )
        scheduling_request.panel_interviewers.set(panel_interviewers)
        has_common_slot = scheduling_request_has_common_slot(scheduling_request)
        if has_common_slot:
            scheduling_request.invitation_sent_at = timezone.now()
            scheduling_request.save(update_fields=['invitation_sent_at', 'updated_at'])
            create_notification(
                application.applicant,
                'interview_self_scheduling',
                f'Choose an interview time for {application.job.title}',
                f'Please choose an interview slot for {application.job.title}.',
                related_entity=scheduling_request,
            )
        for panel_interviewer in panel_interviewers:
            create_notification(
                panel_interviewer,
                'interview_self_scheduling',
                'Panel interview availability required' if not has_common_slot else 'Panel interview scheduling request created',
                (
                    'No common availability timeslot exists for the assigned panel. Update your availability before the applicant can be invited.'
                    if not has_common_slot
                    else f'{request.user.full_name} invited {application.applicant.full_name} to choose a panel interview slot.'
                ),
                related_entity=scheduling_request,
            )
        return Response(InterviewSchedulingRequestSerializer(scheduling_request, context={'request': request}).data, status=status.HTTP_201_CREATED)


class InterviewSchedulingRequestListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scheduling_requests = visible_scheduling_requests_for(request.user)
        return Response(InterviewSchedulingRequestSerializer(scheduling_requests, many=True, context={'request': request}).data)


def book_scheduling_request(request, scheduling_request):
    if scheduling_request.status != InterviewSchedulingRequest.Status.PENDING:
        raise ValidationError({'status': 'Only pending scheduling requests can be booked.'})
    if scheduling_request.expires_at and scheduling_request.expires_at <= timezone.now():
        scheduling_request.status = InterviewSchedulingRequest.Status.EXPIRED
        scheduling_request.save(update_fields=['status', 'updated_at'])
        raise ValidationError({'expires_at': 'This scheduling request has expired.'})
    serializer = BookSchedulingRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    slot = None
    selected_start = selected_end = selected_date = None
    selected_mode = serializer.validated_data.get('mode', Interview.Mode.ONLINE)
    selected_location = serializer.validated_data.get('location', '')
    panel = panel_interviewers_for_scheduling_request(scheduling_request)
    if serializer.validated_data.get('slot_id'):
        if len(panel) > 1:
            raise ValidationError({'slot_id': 'Panel interviews must use a common generated availability slot.'})
        slot = get_object_or_404(
            InterviewerAvailabilitySlot.objects.select_for_update(),
            id=serializer.validated_data['slot_id'],
            organization=scheduling_request.organization,
            interviewer=scheduling_request.interviewer,
        )
        if slot.status != InterviewerAvailabilitySlot.Status.AVAILABLE:
            raise ValidationError({'slot_id': 'Selected interview slot is no longer available.'})
        if slot.start_datetime <= timezone.now():
            raise ValidationError({'slot_id': 'Selected interview slot is in the past.'})
        if Interview.objects.filter(availability_slot=slot).exists():
            raise ValidationError({'slot_id': 'Selected interview slot is already linked to another interview.'})
        selected_start = slot.start_datetime
        selected_end = slot.end_datetime
        selected_date = timezone.localdate(slot.start_datetime)
    else:
        selected_date = serializer.validated_data['interview_date']
        pattern_id = serializer.validated_data['pattern_id']
        start_time = serializer.validated_data['start_time'].replace(microsecond=0)
        end_time = serializer.validated_data['end_time'].replace(microsecond=0)
        matching_slots, _legacy_slots = selectable_slots_for_scheduling_request(scheduling_request)
        generated = next((item for item in matching_slots if item.pattern_id == pattern_id and item.date == selected_date and item.start_time == start_time and item.end_time == end_time), None)
        if not generated:
            raise ValidationError({'slot_id': 'Selected generated interview slot is no longer available.'})
        selected_start = generated.start_datetime
        selected_end = generated.end_datetime
        if selected_start <= timezone.now():
            raise ValidationError({'slot_id': 'Selected interview slot is in the past.'})
        selected_mode = generated.mode
        selected_location = selected_location or generated.location
        if selected_mode == Interview.Mode.PHYSICAL and not selected_location:
            selected_location = 'To be confirmed'
        if active_interview_conflict_exists(
            panel,
            scheduling_request.organization,
            selected_date,
            start_time,
            end_time,
        ):
            raise ValidationError({'slot_id': 'Selected interview slot is already booked.'})

    interview, created = get_or_create_application_interview(
        scheduling_request.application,
        {
            'organization': scheduling_request.organization,
            'recruiter': scheduling_request.recruiter,
            'interviewer': scheduling_request.interviewer,
            'status': Interview.Status.INVITED,
        },
    )
    interview.organization = scheduling_request.organization
    interview.recruiter = scheduling_request.recruiter
    interview.interviewer = scheduling_request.interviewer
    interview.scheduled_datetime = selected_start
    interview.interview_date = selected_date
    interview.start_time = selected_start.time().replace(microsecond=0)
    interview.end_time = selected_end.time().replace(microsecond=0)
    interview.availability_slot = slot
    interview.scheduling_method = Interview.SchedulingMethod.SELF_SCHEDULED
    interview.mode = selected_mode
    # Online meeting links are generated by Google Calendar during event sync.
    # Never persist client-provided placeholders or carry links into non-online interviews.
    interview.meeting_link = ''
    interview.location = selected_location
    interview.save(update_fields=[
        'organization', 'recruiter', 'interviewer', 'scheduled_datetime', 'interview_date', 'start_time', 'end_time', 'availability_slot',
        'scheduling_method', 'mode', 'meeting_link', 'location', 'updated_at',
    ])
    interview.panel_interviewers.set(scheduling_request.panel_interviewers.all())
    interview.change_status(Interview.Status.SCHEDULED, changed_by=request.user, note='Applicant self-scheduled the interview.')

    if slot:
        slot.status = InterviewerAvailabilitySlot.Status.BOOKED
        slot.save(update_fields=['status', 'updated_at'])
    scheduling_request.status = InterviewSchedulingRequest.Status.SCHEDULED
    scheduling_request.selected_slot = slot
    scheduling_request.interview = interview
    scheduling_request.save(update_fields=['status', 'selected_slot', 'interview', 'updated_at'])
    change_application_status(
        scheduling_request.application,
        JobApplication.Status.UNDER_REVIEW,
        request.user,
        'Applicant selected an interview slot.',
    )
    try:
        sync_calendar_event_for_interview(interview)
    except Exception:
        logger.exception(
            'Skipping Google Calendar sync for self-scheduled interview %s.',
            interview.id,
        )

    transaction.on_commit(
        lambda: create_interview_booking_side_effects(scheduling_request, interview, request.user)
    )
    return scheduling_request


class BookSchedulingRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, scheduling_request_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can choose interview slots.')
        scheduling_request = get_object_or_404(
            bookable_scheduling_requests_for_applicant(request.user).select_for_update(),
            id=scheduling_request_id,
        )
        scheduling_request = book_scheduling_request(request, scheduling_request)
        return Response(InterviewSchedulingRequestSerializer(scheduling_request, context={'request': request}).data)


class ApplicationAvailableInterviewDatesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can view available interview dates.')
        scheduling_request = pending_scheduling_request_for_applicant_application_or_404(request.user, application_id)
        generated_slots, legacy_slots = selectable_slots_for_scheduling_request(scheduling_request)
        counts = defaultdict(int)
        for slot in generated_slots:
            counts[slot.date] += 1
        for slot in legacy_slots:
            counts[timezone.localdate(slot.start_datetime)] += 1
        return Response([
            {
                'date': slot_date,
                'day_of_week': slot_date.strftime('%A'),
                'available_slot_count': count,
            }
            for slot_date, count in sorted(counts.items())
        ])


class ApplicationAvailableInterviewSlotsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can view available interview slots.')
        date_value = request.query_params.get('date')
        if not date_value:
            raise ValidationError({'date': 'Date query parameter is required.'})
        try:
            selected_date = datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError as exc:
            raise ValidationError({'date': 'Date must use YYYY-MM-DD format.'}) from exc
        scheduling_request = pending_scheduling_request_for_applicant_application_or_404(request.user, application_id)
        generated_slots, legacy_slots = selectable_slots_for_scheduling_request(scheduling_request, selected_date=selected_date)
        panel = panel_interviewers_for_scheduling_request(scheduling_request)
        data = [serialize_generated_slot_for_selection(slot, scheduling_request.interviewer, panel) for slot in generated_slots]
        data += [serialize_legacy_slot_for_selection(slot, scheduling_request.interviewer, panel) for slot in legacy_slots]
        return Response(sorted(data, key=lambda item: item['start_datetime']))


class ApplicationBookInterviewSlotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, application_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can book interview slots.')
        scheduling_request = pending_scheduling_request_for_applicant_application_or_404(
            request.user,
            application_id,
        )
        scheduling_request = InterviewSchedulingRequest.objects.select_for_update().get(id=scheduling_request.id)
        scheduling_request = book_scheduling_request(request, scheduling_request)
        return Response(InterviewSchedulingRequestSerializer(scheduling_request, context={'request': request}).data)


class InterviewListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interviews = visible_interviews_for(request.user)
        job_id = request.query_params.get('job_id')
        if job_id:
            if not job_id.isdigit():
                raise ValidationError({'job_id': 'Job ID must be a positive integer.'})
            interviews = interviews.filter(application__job_id=job_id)
        interview_status = request.query_params.get('status')
        if interview_status:
            if interview_status not in Interview.Status.values:
                raise ValidationError({'status': 'Select a valid interview status.'})
            interviews = interviews.filter(status=interview_status)
        mode = request.query_params.get('mode')
        if mode:
            if mode not in Interview.Mode.values:
                raise ValidationError({'mode': 'Select a valid interview mode.'})
            interviews = interviews.filter(mode=mode)
        for parameter, lookup in (('date_from', 'scheduled_datetime__date__gte'), ('date_to', 'scheduled_datetime__date__lte')):
            value = request.query_params.get(parameter)
            if value:
                parsed = parse_date(value)
                if not parsed:
                    raise ValidationError({parameter: 'Enter a valid date in YYYY-MM-DD format.'})
                interviews = interviews.filter(**{lookup: parsed})
        search = request.query_params.get('search', '').strip()
        if search:
            interviews = interviews.filter(
                Q(application__applicant__full_name__icontains=search)
                | Q(application__job__title__icontains=search)
                | Q(interviewer__full_name__icontains=search)
                | Q(panel_interviewers__full_name__icontains=search)
                | Q(meeting_link__icontains=search)
                | Q(location__icontains=search)
            ).distinct()
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
        if application.status in (JobApplication.Status.REJECTED, JobApplication.Status.REJECTED):
            raise ValidationError({'status': 'Withdrawn or rejected applications cannot be assigned for interview.'})

        serializer = AssignInterviewerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interviewers = [
            active_interviewer_for_organization_or_404(interviewer_id, application.job.organization)
            for interviewer_id in serializer.validated_data['interviewer_ids']
        ]
        interviewer = interviewers[0]

        application.assigned_interviewer = interviewer
        update_fields = ['assigned_interviewer', 'updated_at']
        if application.status != JobApplication.Status.UNDER_REVIEW:
            previous_status = application.status
            application.status = JobApplication.Status.UNDER_REVIEW
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
                'status': Interview.Status.INVITED,
            },
        )
        previous_interviewer = interview.interviewer
        if not created:
            interview.organization = application.job.organization
            interview.recruiter = request.user
            interview.interviewer = interviewer
            interview.save(update_fields=['organization', 'recruiter', 'interviewer', 'updated_at'])
        interview.panel_interviewers.set(interviewers)
        if created:
            interview.change_status(Interview.Status.INVITED, changed_by=request.user, note='Interview assigned.')
        elif previous_interviewer != interviewer:
            # Keep status unchanged but record assignment notes as a history row for traceability.
            interview.status_history.create(
                from_status=interview.status,
                to_status=interview.status,
                changed_by=request.user,
                note=f'Interviewer reassigned to {interviewer.full_name}.',
            )

        # Assigning an interviewer is the recruiter action that starts the
        # applicant self-scheduling flow.  Previously this endpoint only
        # created the Interview, so the Flutter scheduling-request endpoint
        # had no request to return unless the recruiter performed a second,
        # separate API action.
        scheduling_request, scheduling_request_created = InterviewSchedulingRequest.objects.get_or_create(
            interview=interview,
            defaults={
                'application': application,
                'organization': application.job.organization,
                'recruiter': request.user,
                'interviewer': interviewer,
            },
        )
        if not scheduling_request_created and scheduling_request.status == InterviewSchedulingRequest.Status.PENDING:
            scheduling_request.application = application
            scheduling_request.organization = application.job.organization
            scheduling_request.recruiter = request.user
            scheduling_request.interviewer = interviewer
            scheduling_request.save(update_fields=[
                'application', 'organization', 'recruiter', 'interviewer', 'updated_at',
            ])
        if scheduling_request.status == InterviewSchedulingRequest.Status.PENDING:
            scheduling_request.panel_interviewers.set(interviewers)

        if (
            scheduling_request.status == InterviewSchedulingRequest.Status.PENDING
            and scheduling_request.invitation_sent_at is None
            and scheduling_request_has_common_slot(scheduling_request)
        ):
            scheduling_request.invitation_sent_at = timezone.now()
            scheduling_request.save(update_fields=['invitation_sent_at', 'updated_at'])
            create_notification(
                application.applicant,
                'interview_self_scheduling',
                f'Choose an interview time for {application.job.title}',
                f'Please choose an interview slot for {application.job.title}.',
                related_entity=scheduling_request,
            )

        for panel_interviewer in interviewers:
            create_notification(
                panel_interviewer,
                'interview_assignment',
                f'Interview assignment: {application.applicant.full_name} for {application.job.title}',
                f'You were assigned to interview {application.applicant.full_name} for {application.job.title}.',
                related_entity=interview,
            )
        return Response(InterviewSerializer(interview, context={'request': request}).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
