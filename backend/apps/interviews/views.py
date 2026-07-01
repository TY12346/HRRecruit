"""Role-protected and organization-isolated interview management APIs."""

import logging
from collections import defaultdict
from datetime import datetime

from django.db import IntegrityError, transaction
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
from .slot_generation import generate_available_slots


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
        except GoogleCalendarConfigurationError as exc:
            raise ValidationError({'google_calendar': str(exc)}) from exc
        sync_result = sync_existing_google_events_for_user(request.user)
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
    ).prefetch_related('status_history', 'calendar_events')


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
    )
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        if membership:
            return requests.filter(organization=membership.organization, recruiter=user)
    if user.role == User.Role.INTERVIEWER:
        membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
        if membership:
            return requests.filter(organization=membership.organization, interviewer=user)
    if user.role == User.Role.APPLICANT:
        return requests.filter(application__applicant=user)
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
    ).filter(application__applicant=applicant)


def available_slots_for_interviewer(user):
    membership = get_active_membership(user, OrganizationMembership.Role.INTERVIEWER)
    if not membership:
        raise PermissionDenied('Interviewer must belong to an active organization.')
    return InterviewerAvailabilitySlot.objects.filter(organization=membership.organization, interviewer=user)



def pending_scheduling_request_for_applicant_application_or_404(applicant, application_id):
    return get_object_or_404(
        bookable_scheduling_requests_for_applicant(applicant),
        application_id=application_id,
        status=InterviewSchedulingRequest.Status.PENDING,
    )


def selectable_slots_for_scheduling_request(scheduling_request, selected_date=None):
    generated_slots = generate_available_slots(scheduling_request.interviewer, scheduling_request.organization)
    if selected_date:
        generated_slots = [slot for slot in generated_slots if slot.date == selected_date]
    legacy_slots = InterviewerAvailabilitySlot.objects.filter(
        organization=scheduling_request.organization,
        interviewer=scheduling_request.interviewer,
        status=InterviewerAvailabilitySlot.Status.AVAILABLE,
        start_datetime__gt=timezone.now(),
    ).order_by('start_datetime')
    if selected_date:
        legacy_slots = [slot for slot in legacy_slots if timezone.localdate(slot.start_datetime) == selected_date]
    return generated_slots, legacy_slots


def serialize_generated_slot_for_selection(slot, interviewer):
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
        'interviewer_names': [interviewer.full_name] if interviewer else [],
        'status': slot.status,
    }


def serialize_legacy_slot_for_selection(slot, interviewer):
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
        'interviewer_names': [interviewer.full_name] if interviewer else [],
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
            'Interview slot selected',
            f'{applicant.full_name} selected an interview slot for {scheduling_request.application.job.title}.',
        ),
        (
            scheduling_request.interviewer,
            'Interview slot selected',
            f'{applicant.full_name} selected your available interview slot.',
        ),
    ]
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
        if application.status in (JobApplication.Status.WITHDRAWN, JobApplication.Status.REJECTED):
            raise ValidationError({'status': 'Withdrawn or rejected applications cannot be scheduled for interview.'})
        serializer = CreateSchedulingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interviewer = active_interviewer_for_organization_or_404(
            serializer.validated_data['interviewer_id'],
            application.job.organization,
        )

        application.assigned_interviewer = interviewer
        if application.status != JobApplication.Status.SHORTLISTED:
            previous_status = application.status
            application.status = JobApplication.Status.SHORTLISTED
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

        interview, interview_created = Interview.objects.get_or_create(
            application=application,
            defaults={
                'organization': application.job.organization,
                'recruiter': request.user,
                'interviewer': interviewer,
                'status': Interview.Status.ASSIGNED,
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
        if interview_created:
            interview.status_history.create(
                from_status=Interview.Status.ASSIGNED,
                to_status=Interview.Status.ASSIGNED,
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
        create_notification(
            application.applicant,
            'interview_self_scheduling',
            'Interview scheduling request',
            f'Please choose an interview slot for {application.job.title}.',
            related_entity=scheduling_request,
        )
        create_notification(
            interviewer,
            'interview_self_scheduling',
            'Interview scheduling request created',
            f'{request.user.full_name} invited {application.applicant.full_name} to choose one of your available interview slots.',
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
    selected_meeting_link = serializer.validated_data.get('meeting_link', '')
    selected_location = serializer.validated_data.get('location', '')
    if serializer.validated_data.get('slot_id'):
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
        matching_slots = generate_available_slots(scheduling_request.interviewer, scheduling_request.organization)
        generated = next((item for item in matching_slots if item.pattern_id == pattern_id and item.date == selected_date and item.start_time == start_time and item.end_time == end_time), None)
        if not generated:
            raise ValidationError({'slot_id': 'Selected generated interview slot is no longer available.'})
        selected_start = generated.start_datetime
        selected_end = generated.end_datetime
        selected_mode = generated.mode
        selected_meeting_link = selected_meeting_link or generated.meeting_link
        selected_location = selected_location or generated.location
        if Interview.objects.select_for_update().filter(
            organization=scheduling_request.organization,
            interviewer=scheduling_request.interviewer,
            interview_date=selected_date,
            start_time=start_time,
            end_time=end_time,
            status__in=[Interview.Status.ASSIGNED, Interview.Status.SCHEDULED],
        ).exists():
            raise ValidationError({'slot_id': 'Selected interview slot is already booked.'})

    interview, created = Interview.objects.get_or_create(
        application=scheduling_request.application,
        defaults={
            'organization': scheduling_request.organization,
            'recruiter': scheduling_request.recruiter,
            'interviewer': scheduling_request.interviewer,
            'status': Interview.Status.ASSIGNED,
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
    interview.meeting_link = selected_meeting_link
    interview.location = selected_location
    interview.save(update_fields=[
        'organization', 'recruiter', 'interviewer', 'scheduled_datetime', 'interview_date', 'start_time', 'end_time', 'availability_slot',
        'scheduling_method', 'mode', 'meeting_link', 'location', 'updated_at',
    ])
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
        JobApplication.Status.INTERVIEW_ACCEPTED,
        request.user,
        'Applicant selected an interview slot.',
    )
    try:
        sync_calendar_event_for_interview(interview)
    except (GoogleCalendarConfigurationError, GoogleCalendarSyncError):
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
        data = [serialize_generated_slot_for_selection(slot, scheduling_request.interviewer) for slot in generated_slots]
        data += [serialize_legacy_slot_for_selection(slot, scheduling_request.interviewer) for slot in legacy_slots]
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
