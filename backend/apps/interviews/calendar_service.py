"""Calendar event helpers for accepted interviews.

The interview flow supports real Google Calendar OAuth when it is explicitly
configured, but it still keeps the FYP demo usable without external services.
If Google OAuth is unavailable or a recruiter has not connected Google, the
service falls back to either a Google template link or a local placeholder
CalendarEvent record.
"""

import os
from datetime import datetime, timedelta
from importlib import import_module, util
from urllib.parse import urlencode, urlparse

from django.core import signing
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode

from .models import CalendarEvent, GoogleCalendarCredential, Interview

GOOGLE_CALENDAR_RENDER_URL = 'https://calendar.google.com/calendar/render'
GOOGLE_CALENDAR_TOKEN_URI = 'https://oauth2.googleapis.com/token'
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.events']
GOOGLE_CALENDAR_STATE_SALT = 'hrrecruit.google-calendar-oauth'
DEFAULT_INTERVIEW_DURATION_MINUTES = 60


class GoogleCalendarConfigurationError(RuntimeError):
    """Raised when real Google Calendar OAuth is requested but unavailable."""


class GoogleCalendarSyncError(RuntimeError):
    """Raised when Google Calendar event sync fails."""


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes', 'on')


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
        os.getenv('GOOGLE_CALENDAR_CLIENT_ID', '').strip()
        and os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', '').strip()
    )


def google_calendar_redirect_uri():
    return os.getenv('GOOGLE_CALENDAR_REDIRECT_URI', '').strip()


def google_calendar_link_enabled():
    """Return whether Google Calendar integration is enabled for the demo."""
    return _env_flag('GOOGLE_CALENDAR_ENABLED', default=False)


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
        'fallback_mode': _calendar_fallback_mode(),
    }


def _google_client_config():
    if not google_calendar_credentials_configured() or not google_calendar_redirect_uri():
        raise GoogleCalendarConfigurationError(
            'Set GOOGLE_CALENDAR_ENABLED=true, GOOGLE_CALENDAR_CLIENT_ID, '
            'GOOGLE_CALENDAR_CLIENT_SECRET, and GOOGLE_CALENDAR_REDIRECT_URI to use Google Calendar OAuth.'
        )
    return {
        'web': {
            'client_id': os.getenv('GOOGLE_CALENDAR_CLIENT_ID', '').strip(),
            'client_secret': os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', '').strip(),
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


def _is_local_oauth_redirect_host(hostname):
    if hostname in ('localhost', '127.0.0.1', '10.0.2.2'):
        return True
    if hostname.startswith(('192.168.', '10.')):
        return True
    parts = hostname.split('.')
    if len(parts) == 4 and parts[0] == '172':
        try:
            second_octet = int(parts[1])
        except ValueError:
            return False
        return 16 <= second_octet <= 31
    return False


def _allow_local_http_oauth_for_local_redirects():
    """Allow OAuthLib HTTP redirects for localhost/local-network demo setups."""
    redirect_uri = google_calendar_redirect_uri()
    parsed_uri = urlparse(redirect_uri)
    if (
        parsed_uri.scheme == 'http'
        and _is_local_oauth_redirect_host(parsed_uri.hostname or '')
    ):
        os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')


def _flow_from_client_config(state=None):
    _require_google_oauth_ready()
    _allow_local_http_oauth_for_local_redirects()
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
            'client_id': credentials.client_id or os.getenv('GOOGLE_CALENDAR_CLIENT_ID', '').strip(),
            'client_secret': credentials.client_secret or os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', '').strip(),
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
    return credentials_module.Credentials(
        token=credential.access_token,
        refresh_token=credential.refresh_token or None,
        token_uri=credential.token_uri or GOOGLE_CALENDAR_TOKEN_URI,
        client_id=credential.client_id or os.getenv('GOOGLE_CALENDAR_CLIENT_ID', '').strip(),
        client_secret=credential.client_secret or os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', '').strip(),
        scopes=credential.scopes or GOOGLE_CALENDAR_SCOPES,
    )


def _google_calendar_service(credentials):
    discovery_module = import_module('googleapiclient.discovery')
    return discovery_module.build('calendar', 'v3', credentials=credentials, cache_discovery=False)


def _fetch_google_calendar_primary_email(credentials):
    service = _google_calendar_service(credentials)
    calendar = service.calendarList().get(calendarId='primary').execute()
    return calendar.get('id', '')


def _format_google_datetime(value):
    """Format an aware datetime for Google Calendar template links."""
    return value.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def _interview_end_datetime(interview):
    if interview.end_time and interview.interview_date:
        end_datetime = timezone.make_aware(
            datetime.combine(interview.interview_date, interview.end_time),
            timezone.get_current_timezone(),
        )
        if interview.scheduled_datetime and end_datetime > interview.scheduled_datetime:
            return end_datetime
    duration_minutes = int(
        os.getenv('GOOGLE_CALENDAR_DEFAULT_DURATION_MINUTES', DEFAULT_INTERVIEW_DURATION_MINUTES)
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


def _google_event_body(interview):
    if not interview.scheduled_datetime:
        raise ValueError('Interview must be scheduled before creating a calendar event.')
    return {
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
    }


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

    start = _format_google_datetime(interview.scheduled_datetime)
    end = _format_google_datetime(_interview_end_datetime(interview))
    query = urlencode(
        {
            'action': 'TEMPLATE',
            'text': _event_summary(interview),
            'dates': f'{start}/{end}',
            'details': _event_description(interview),
            'location': _event_location(interview),
        }
    )
    return f'{GOOGLE_CALENDAR_RENDER_URL}?{query}'


def _calendar_fallback_mode():
    if google_calendar_link_enabled() and google_calendar_credentials_configured():
        return 'google_template_link'
    return 'local_placeholder'


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
        ).execute()
    else:
        google_event = service.events().insert(
            calendarId='primary',
            body=event_body,
        ).execute()

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


def _save_failed_google_event(interview, message=''):
    return CalendarEvent.objects.update_or_create(
        interview=interview,
        provider='google_calendar',
        defaults={
            'calendar_link': '',
            'sync_status': CalendarEvent.SyncStatus.FAILED,
            'last_synced_at': timezone.now(),
        },
    )[0]


def _save_google_template_event(interview):
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


def _save_local_event(interview):
    return CalendarEvent.objects.update_or_create(
        interview=interview,
        provider='local',
        defaults={
            'calendar_link': build_local_calendar_link(interview),
            'sync_status': CalendarEvent.SyncStatus.NOT_SYNCED,
            'last_synced_at': None,
        },
    )[0]


def sync_calendar_event_for_interview(interview):
    """Create/update the CalendarEvent for an accepted interview.

    Real Google Calendar event insertion is used only when OAuth is enabled,
    dependencies are installed, and the recruiter has connected Google. Without
    that, HRRecruit keeps the workflow usable through the previous template-link
    or local-placeholder fallback.
    """
    if google_calendar_oauth_ready():
        credential = GoogleCalendarCredential.objects.filter(user=interview.recruiter).first()
        if credential:
            try:
                return _sync_real_google_calendar_event(interview, credential)
            except Exception as exc:
                _save_failed_google_event(interview, message=str(exc))
                raise GoogleCalendarSyncError('Failed to sync Google Calendar event.') from exc

    if google_calendar_link_enabled() and google_calendar_credentials_configured():
        return _save_google_template_event(interview)

    return _save_local_event(interview)
