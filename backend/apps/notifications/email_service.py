"""Email delivery helpers for HRRecruit notifications.

SendGrid is optional for FYP development. When SendGrid credentials are not
configured, the service falls back to Django's configured email backend, which is
console email by default in local development.
"""

import json
from urllib import request as urlrequest
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

from django.conf import settings
from django.core.mail import send_mail


SENDGRID_MAIL_SEND_URL = 'https://api.sendgrid.com/v3/mail/send'
DEFAULT_CONSOLE_FROM_EMAIL = 'no-reply@hrrecruit.local'


def _from_email():
    return (
        getattr(settings, 'SENDGRID_FROM_EMAIL', '')
        or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        or DEFAULT_CONSOLE_FROM_EMAIL
    )


def _sendgrid_api_key():
    return getattr(settings, 'SENDGRID_API_KEY', '') or ''


def _sendgrid_configured():
    return bool(_sendgrid_api_key() and getattr(settings, 'SENDGRID_FROM_EMAIL', ''))


def _send_via_console(subject, message, recipient_list):
    sent_count = send_mail(
        subject=subject,
        message=message,
        from_email=_from_email(),
        recipient_list=recipient_list,
        fail_silently=False,
    )
    return {'provider': 'console', 'sent_count': sent_count}


def _send_via_sendgrid(subject, message, recipient_list):
    payload = {
        'personalizations': [{'to': [{'email': email} for email in recipient_list]}],
        'from': {'email': _from_email()},
        'subject': subject,
        'content': [{'type': 'text/plain', 'value': message}],
    }
    encoded_payload = json.dumps(payload).encode('utf-8')
    mail_request = urlrequest.Request(
        SENDGRID_MAIL_SEND_URL,
        data=encoded_payload,
        headers={
            'Authorization': f'Bearer {_sendgrid_api_key()}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with urlrequest.urlopen(mail_request, timeout=10) as response:
        return {'provider': 'sendgrid', 'status_code': response.status}


def send_email(subject, message, recipient_list):
    """Send a plain-text email through SendGrid or the console fallback.

    Tests mock the SendGrid transport and this function never requires SendGrid
    settings for local development. Provider errors also fall back to the console
    backend so application flows can continue without external email delivery.
    """
    recipients = [email for email in recipient_list if email]
    if not recipients:
        return {'provider': 'none', 'sent_count': 0}

    if not _sendgrid_configured():
        return _send_via_console(subject, message, recipients)

    try:
        return _send_via_sendgrid(subject, message, recipients)
    except (HTTPError, URLError, TimeoutError, OSError):
        return _send_via_console(subject, message, recipients)


def send_password_reset_otp_email(user, otp_code):
    reset_base_url = getattr(settings, 'FRONTEND_PASSWORD_RESET_URL', '') or 'http://localhost:5173/forgot-password'
    reset_link = f'{reset_base_url}?{urlencode({"email": user.email, "otp": otp_code})}'
    return send_email(
        subject='HRRecruit Password Reset',
        message=(
            f'Hello {user.full_name},\n\n'
            'Use the link below to reset your HRRecruit password:\n'
            f'{reset_link}\n\n'
            f'If the link does not open the app, enter this reset code manually: {otp_code}.\n'
            'This reset code expires in 10 minutes.'
        ),
        recipient_list=[user.email],
    )


def send_team_account_created_email(user, temporary_password):
    role_label = user.get_role_display() if hasattr(user, 'get_role_display') else user.role
    return send_email(
        subject='Your HRRecruit team account',
        message=(
            f'Hello {user.full_name},\n\n'
            f'An HRRecruit {role_label} team account has been created for you.\n'
            f'Email: {user.email}\n'
            f'Temporary password: {temporary_password}\n\n'
            'Please log in and change your password.'
        ),
        recipient_list=[user.email],
    )


def send_interview_invitation_email(invitation):
    interview = invitation.interview
    application = interview.application
    return send_email(
        subject=f'Interview invitation for {application.job.title}',
        message=(
            f'Hello {application.applicant.full_name},\n\n'
            f'You have a new interview invitation for {application.job.title}.\n'
            f'Proposed time: {invitation.proposed_datetime}\n'
            f'Mode: {invitation.get_mode_display()}\n'
            f'Meeting link: {invitation.meeting_link or "N/A"}\n'
            f'Location: {invitation.location or "N/A"}\n\n'
            'Please review and respond in HRRecruit.'
        ),
        recipient_list=[application.applicant.email],
    )


def send_job_offer_email(offer):
    application = offer.application
    return send_email(
        subject=f'Job offer for {application.job.title}',
        message=(
            f'Hello {application.applicant.full_name},\n\n'
            f'You received a job offer for {application.job.title}.\n'
            f'Response deadline: {offer.respond_deadline}\n\n'
            f'{offer.offer_message}\n\n'
            'Please accept or decline the offer in HRRecruit.'
        ),
        recipient_list=[application.applicant.email],
    )


def send_subscription_reminder_email(user, subscription):
    return send_email(
        subject='HRRecruit subscription reminder',
        message=(
            f'Hello {user.full_name},\n\n'
            f'Your {subscription.plan.name} subscription for {subscription.organization.name} '
            f'ends on {subscription.end_date}.\n'
            'Please renew or upgrade your plan in HRRecruit if needed.'
        ),
        recipient_list=[user.email],
    )
