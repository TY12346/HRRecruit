"""Calendar event helpers for accepted interviews.

The interview flow uses real Google Calendar OAuth/API integration. If Google
OAuth, credentials, dependencies, or a connected account are missing, scheduling
raises a clear error instead of creating placeholder events.
"""

from datetime import datetime, timedelta
from uuid import uuid4
from importlib import import_module, util

from django.conf import settings
from django.core import signing
from django.utils import timezone

from .models import CalendarEvent, GoogleCalendarCredential, Interview

GOOGLE_CALENDAR_TOKEN_URI = 'https://oauth2.googleapis.com/token'
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.events']
GOOGLE_CALENDAR_STATE_SALT = 'hrrecruit.google-calendar-oauth'
DEFAULT_INTERVIEW_DURATION_MINUTES = 60


class GoogleCalendarConfigurationError(RuntimeError):
    """Raised when real Google Calendar OAuth is requested but unavailable."""


class GoogleCalendarSyncError(RuntimeError):
    """Raised when Google Calendar event sync fails."""


def _optional_google_dependencies_available():
    module_names = [
        'google_auth_oauthlib',
        'google_auth_oauthlib.flow',
        'google',
        'google.oauth2',
        'google.oauth2.credentials',
        'googleapiclient',
        'googleapiclient.discovery',
    ]
    return all(util.find_spec(module_name) is not None for module_name in module_names)


def google_calendar_credentials_configured():
    """Return True only when Google OAuth client settings are present."""
    return bool(
        getattr(settings, 'GOOGLE_CALENDAR_CLIENT_ID', '').strip()
        and getattr(settings, 'GOOGLE_CALENDAR_CLIENT_SECRET', '').strip()
    )


def google_calendar_redirect_uri():
    return getattr(settings, 'GOOGLE_CALENDAR_REDIRECT_URI', '').strip()


def google_calendar_link_enabled():
    """Return whether Google Calendar API integration is enabled."""
    return bool(getattr(settings, 'GOOGLE_CALENDAR_ENABLED', False))


def google_calendar_oauth_ready():
    """Return whether real Google Calendar OAuth can be used."""
    return bool(
        google_calendar_link_enabled()
        and google_calendar_credentials_configured()
        and google_calendar_redirect_uri()
        and _optional_google_dependencies_available()
    )


def google_calendar_status_for_user(user):
    """Return a safe status payload for recruiter UI connection cards."""
    credential = GoogleCalendarCredential.objects.filter(user=user).first()
    return {
        'enabled': google_calendar_link_enabled(),
        'client_configured': google_calendar_credentials_configured(),
        'redirect_uri_configured': bool(google_calendar_redirect_uri()),
        'dependencies_installed': _optional_google_dependencies_available(),
        'oauth_ready': google_calendar_oauth_ready(),
        'connected': bool(credential),
        'connected_email': credential.google_account_email if credential else '',
        'last_synced_at': credential.last_synced_at if credential else None,
    }


def _google_client_config():
    if not google_calendar_credentials_configured() or not google_calendar_redirect_uri():
        raise GoogleCalendarConfigurationError(
            'Set GOOGLE_CALENDAR_ENABLED=true, GOOGLE_CALENDAR_CLIENT_ID, '
            'GOOGLE_CALENDAR_CLIENT_SECRET, and GOOGLE_CALENDAR_REDIRECT_URI to use Google Calendar OAuth.'
        )
    return {
        'web': {
            'client_id': getattr(settings, 'GOOGLE_CALENDAR_CLIENT_ID', '').strip(),
            'client_secret': getattr(settings, 'GOOGLE_CALENDAR_CLIENT_SECRET', '').strip(),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': GOOGLE_CALENDAR_TOKEN_URI,
            'redirect_uris': [google_calendar_redirect_uri()],
        }
    }


def _require_google_oauth_ready():
    if not google_calendar_oauth_ready():
        raise GoogleCalendarConfigurationError(
            'Google Calendar OAuth is not ready. Enable it, configure client credentials and redirect URI, '
            'and install google-api-python-client, google-auth, and google-auth-oauthlib.'
        )


def _flow_from_client_config(state=None):
    _require_google_oauth_ready()
    flow_module = import_module('google_auth_oauthlib.flow')
    flow = flow_module.Flow.from_client_config(
        _google_client_config(),
        scopes=GOOGLE_CALENDAR_SCOPES,
        state=state,
    )
    flow.redirect_uri = google_calendar_redirect_uri()
    return flow


def build_google_calendar_oauth_state(user, next_url=''):
    return signing.dumps(
        {'user_id': user.id, 'next': next_url or ''},
        salt=GOOGLE_CALENDAR_STATE_SALT,
    )


def validate_google_calendar_oauth_state(state, user):
    try:
        payload = signing.loads(state, salt=GOOGLE_CALENDAR_STATE_SALT, max_age=600)
    except signing.BadSignature as exc:
        raise GoogleCalendarConfigurationError('Invalid or expired Google Calendar OAuth state.') from exc
    if payload.get('user_id') != user.id:
        raise GoogleCalendarConfigurationError('Google Calendar OAuth state does not match the signed-in user.')
    return payload


def build_google_calendar_authorization_url(user, next_url=''):
    """Create a real Google OAuth authorization URL for the signed-in user."""
    state = build_google_calendar_oauth_state(user, next_url=next_url)
    flow = _flow_from_client_config(state=state)
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )
    return authorization_url


def store_google_calendar_credentials(user, code, state):
    """Exchange an OAuth authorization code and persist refreshable credentials."""
    validate_google_calendar_oauth_state(state, user)
    flow = _flow_from_client_config(state=state)
    flow.fetch_token(code=code)
    credentials = flow.credentials
    email = _fetch_google_calendar_primary_email(credentials)
    credential, _ = GoogleCalendarCredential.objects.update_or_create(
        user=user,
        defaults={
            'google_account_email': email,
            'access_token': credentials.token or '',
            'refresh_token': credentials.refresh_token or '',
            'token_uri': credentials.token_uri or GOOGLE_CALENDAR_TOKEN_URI,
            'client_id': credentials.client_id or getattr(settings, 'GOOGLE_CALENDAR_CLIENT_ID', '').strip(),
            'client_secret': credentials.client_secret or getattr(settings, 'GOOGLE_CALENDAR_CLIENT_SECRET', '').strip(),
            'scopes': list(credentials.scopes or GOOGLE_CALENDAR_SCOPES),
            'expiry': credentials.expiry,
        },
    )
    return credential


def disconnect_google_calendar(user):
    deleted_count, _ = GoogleCalendarCredential.objects.filter(user=user).delete()
    return deleted_count > 0


def _credentials_from_model(credential):
    credentials_module = import_module('google.oauth2.credentials')
    credentials = credentials_module.Credentials(
        token=credential.access_token,
        refresh_token=credential.refresh_token or None,
        token_uri=credential.token_uri or GOOGLE_CALENDAR_TOKEN_URI,
        client_id=credential.client_id or getattr(settings, 'GOOGLE_CALENDAR_CLIENT_ID', '').strip(),
        client_secret=credential.client_secret or getattr(settings, 'GOOGLE_CALENDAR_CLIENT_SECRET', '').strip(),
        scopes=credential.scopes or GOOGLE_CALENDAR_SCOPES,
    )
    if getattr(credentials, 'expired', False) and credentials.refresh_token:
        request_module = import_module('google.auth.transport.requests')
        credentials.refresh(request_module.Request())
    return credentials


def _google_calendar_service(credentials):
    discovery_module = import_module('googleapiclient.discovery')
    return discovery_module.build('calendar', 'v3', credentials=credentials, cache_discovery=False)


def _fetch_google_calendar_primary_email(credentials):
    service = _google_calendar_service(credentials)
    calendar = service.calendarList().get(calendarId='primary').execute()
    return calendar.get('id', '')


def _interview_end_datetime(interview):
    if interview.end_time and interview.interview_date:
        end_datetime = timezone.make_aware(
            datetime.combine(interview.interview_date, interview.end_time),
            timezone.get_current_timezone(),
        )
        if interview.scheduled_datetime and end_datetime > interview.scheduled_datetime:
            return end_datetime
    duration_minutes = int(
        getattr(settings, 'GOOGLE_CALENDAR_DEFAULT_DURATION_MINUTES', DEFAULT_INTERVIEW_DURATION_MINUTES)
    )
    return interview.scheduled_datetime + timedelta(minutes=duration_minutes)


def _event_summary(interview):
    return f'Interview: {interview.application.job.title}'


def _event_description(interview):
    applicant = interview.application.applicant
    details = [
        f'HRRecruit interview for {applicant.full_name}.',
        f'Mode: {interview.get_mode_display()}.',
        f'Application ID: {interview.application_id}.',
    ]
    if interview.meeting_link:
        details.append(f'Meeting link: {interview.meeting_link}')
    if interview.location:
        details.append(f'Location: {interview.location}')
    return '\n'.join(details)


def _event_location(interview):
    return interview.meeting_link if interview.mode == Interview.Mode.ONLINE else interview.location


def _timezone_name():
    return getattr(settings, 'TIME_ZONE', 'UTC')


def _event_attendees(interview):
    people = [
        interview.application.applicant,
        interview.interviewer,
        interview.recruiter,
    ]
    seen = set()
    attendees = []
    for person in people:
        email = (getattr(person, 'email', '') or '').strip()
        if not email or email.lower() in seen:
            continue
        seen.add(email.lower())
        attendees.append({'email': email, 'displayName': getattr(person, 'full_name', '') or email})
    return attendees


def _conference_data_for(interview):
    if interview.mode != Interview.Mode.ONLINE or interview.meeting_link:
        return None
    return {
        'createRequest': {
            'requestId': f'hrrecruit-interview-{interview.id}-{uuid4().hex[:12]}',
            'conferenceSolutionKey': {'type': 'hangoutsMeet'},
        }
    }


def _google_event_body(interview):
    if not interview.scheduled_datetime:
        raise ValueError('Interview must be scheduled before creating a calendar event.')
    event_body = {
        'summary': _event_summary(interview),
        'description': _event_description(interview),
        'location': _event_location(interview),
        'start': {
            'dateTime': interview.scheduled_datetime.isoformat(),
            'timeZone': _timezone_name(),
        },
        'end': {
            'dateTime': _interview_end_datetime(interview).isoformat(),
            'timeZone': _timezone_name(),
        },
        'attendees': _event_attendees(interview),
        'reminders': {'useDefault': True},
    }
    conference_data = _conference_data_for(interview)
    if conference_data:
        event_body['conferenceData'] = conference_data
    return event_body


def _sync_real_google_calendar_event(interview, credential):
    credentials = _credentials_from_model(credential)
    service = _google_calendar_service(credentials)
    event_body = _google_event_body(interview)
    existing_event = CalendarEvent.objects.filter(interview=interview, provider='google_calendar').first()
    if existing_event and existing_event.external_event_id:
        google_event = service.events().update(
            calendarId='primary',
            eventId=existing_event.external_event_id,
            body=event_body,
            sendUpdates='all',
            conferenceDataVersion=1,
        ).execute()
    else:
        google_event = service.events().insert(
            calendarId='primary',
            body=event_body,
            sendUpdates='all',
            conferenceDataVersion=1,
        ).execute()

    generated_meet_link = google_event.get('hangoutLink') or ''
    if generated_meet_link and not interview.meeting_link:
        interview.meeting_link = generated_meet_link
        interview.save(update_fields=['meeting_link', 'updated_at'])

    credential.access_token = getattr(credentials, 'token', credential.access_token) or credential.access_token
    credential.expiry = getattr(credentials, 'expiry', credential.expiry)
    credential.last_synced_at = timezone.now()
    credential.save(update_fields=['access_token', 'expiry', 'last_synced_at', 'updated_at'])

    return CalendarEvent.objects.update_or_create(
        interview=interview,
        provider='google_calendar',
        defaults={
            'external_event_id': google_event.get('id', ''),
            'calendar_link': google_event.get('htmlLink', ''),
            'sync_status': CalendarEvent.SyncStatus.SYNCED,
            'last_synced_at': timezone.now(),
        },
    )[0]


def sync_existing_google_events_for_user(user):
    """Sync this recruiter/interviewer's scheduled future interviews after OAuth connect."""
    if not google_calendar_oauth_ready():
        raise GoogleCalendarConfigurationError('Google Calendar OAuth is not ready.')
    credential = GoogleCalendarCredential.objects.filter(user=user).first()
    if not credential:
        return {'synced': 0, 'failed': 0}

    interviews = Interview.objects.select_related(
        'application',
        'application__applicant',
        'application__job',
        'recruiter',
        'interviewer',
    ).filter(status=Interview.Status.SCHEDULED, scheduled_datetime__gte=timezone.now())
    if user.role == 'recruiter':
        interviews = interviews.filter(recruiter=user)
    elif user.role == 'interviewer':
        interviews = interviews.filter(interviewer=user)
    else:
        interviews = interviews.none()

    synced = 0
    for interview in interviews:
        _sync_real_google_calendar_event(interview, credential)
        synced += 1
    return {'synced': synced, 'failed': 0}


def sync_calendar_event_for_interview(interview):
    """Create/update the real Google Calendar event for a scheduled interview."""
    if not google_calendar_oauth_ready():
        raise GoogleCalendarConfigurationError(
            'Google Calendar API is not ready. Configure GOOGLE_CALENDAR_ENABLED, OAuth client credentials, '
            'redirect URI, and Google API dependencies before scheduling interviews.'
        )
    credential = GoogleCalendarCredential.objects.filter(user=interview.recruiter).first()
    if not credential:
        raise GoogleCalendarConfigurationError('Recruiter has not connected Google Calendar.')
    try:
        return _sync_real_google_calendar_event(interview, credential)
    except Exception as exc:
        raise GoogleCalendarSyncError('Failed to sync Google Calendar event.') from exc
