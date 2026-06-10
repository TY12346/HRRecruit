"""Calendar event helpers for accepted interviews.

The FYP demo must keep the interview flow working even when Google Calendar
OAuth is not configured.  This service therefore creates either a Google
Calendar template link (when explicitly enabled and configured) or a local
placeholder CalendarEvent record without making Google API calls.
"""

import os
from datetime import timedelta
from urllib.parse import urlencode

from django.utils import timezone
from django.utils.http import urlsafe_base64_encode

from .models import CalendarEvent, Interview

GOOGLE_CALENDAR_RENDER_URL = 'https://calendar.google.com/calendar/render'
DEFAULT_INTERVIEW_DURATION_MINUTES = 60


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes', 'on')


def google_calendar_credentials_configured():
    """Return True only when optional Google Calendar OAuth config is present."""
    return bool(
        os.getenv('GOOGLE_CALENDAR_CLIENT_ID', '').strip()
        and os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', '').strip()
    )


def google_calendar_link_enabled():
    """Return whether the demo should create Google Calendar template links."""
    return _env_flag('GOOGLE_CALENDAR_ENABLED', default=False)


def _format_google_datetime(value):
    """Format an aware datetime for Google Calendar template links."""
    return value.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def _interview_end_datetime(interview):
    duration_minutes = int(
        os.getenv('GOOGLE_CALENDAR_DEFAULT_DURATION_MINUTES', DEFAULT_INTERVIEW_DURATION_MINUTES)
    )
    return interview.scheduled_datetime + timedelta(minutes=duration_minutes)


def build_local_calendar_link(interview):
    """Return a deterministic local calendar placeholder without external sync."""
    query = urlencode(
        {
            'interview_id': interview.id,
            'application_id': interview.application_id,
            'scheduled_datetime': interview.scheduled_datetime.isoformat() if interview.scheduled_datetime else '',
        }
    )
    token = urlsafe_base64_encode(f'interview:{interview.id}'.encode())
    return f'https://calendar.hrrecruit.local/events/{token}?{query}'


def build_google_calendar_link(interview):
    """Build a Google Calendar event creation URL without calling Google APIs."""
    if not interview.scheduled_datetime:
        raise ValueError('Interview must be scheduled before creating a calendar link.')

    job = interview.application.job
    applicant = interview.application.applicant
    title = f'Interview: {job.title}'
    details = (
        f'HRRecruit interview for {applicant.full_name}.\n'
        f'Mode: {interview.get_mode_display()}.'
    )
    if interview.meeting_link:
        details = f'{details}\nMeeting link: {interview.meeting_link}'

    location = interview.meeting_link if interview.mode == Interview.Mode.ONLINE else interview.location
    start = _format_google_datetime(interview.scheduled_datetime)
    end = _format_google_datetime(_interview_end_datetime(interview))
    query = urlencode(
        {
            'action': 'TEMPLATE',
            'text': title,
            'dates': f'{start}/{end}',
            'details': details,
            'location': location,
        }
    )
    return f'{GOOGLE_CALENDAR_RENDER_URL}?{query}'


def sync_calendar_event_for_interview(interview):
    """Create/update the CalendarEvent for an accepted interview.

    Google Calendar support is optional for the FYP demo. When disabled or when
    OAuth credentials are missing, only a local CalendarEvent is saved. When
    enabled with credentials, a Google Calendar template link is saved and
    marked as synced because the user can open the link without HRRecruit making
    a real Google API call.
    """
    if google_calendar_link_enabled() and google_calendar_credentials_configured():
        try:
            calendar_link = build_google_calendar_link(interview)
        except Exception:
            return CalendarEvent.objects.update_or_create(
                interview=interview,
                provider='google_calendar_link',
                defaults={
                    'calendar_link': '',
                    'sync_status': CalendarEvent.SyncStatus.FAILED,
                    'last_synced_at': timezone.now(),
                },
            )[0]

        return CalendarEvent.objects.update_or_create(
            interview=interview,
            provider='google_calendar_link',
            defaults={
                'calendar_link': calendar_link,
                'sync_status': CalendarEvent.SyncStatus.SYNCED,
                'last_synced_at': timezone.now(),
            },
        )[0]

    return CalendarEvent.objects.update_or_create(
        interview=interview,
        provider='local',
        defaults={
            'calendar_link': build_local_calendar_link(interview),
            'sync_status': CalendarEvent.SyncStatus.NOT_SYNCED,
            'last_synced_at': None,
        },
    )[0]
