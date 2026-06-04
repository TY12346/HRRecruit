"""Small local helpers for early-stage interview calendar placeholders."""

from urllib.parse import urlencode

from django.utils.http import urlsafe_base64_encode



def build_calendar_link(interview):
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
