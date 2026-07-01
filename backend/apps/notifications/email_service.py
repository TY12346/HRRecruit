"""SendGrid email delivery helpers for HRRecruit notifications."""

import json
from urllib import request as urlrequest
from urllib.parse import urlencode, urlsplit, urlunsplit

from django.conf import settings


SENDGRID_MAIL_SEND_URL = 'https://api.sendgrid.com/v3/mail/send'


class SendGridConfigurationError(RuntimeError):
    """Raised when SendGrid email delivery is requested without credentials."""


def _from_email():
    return getattr(settings, 'SENDGRID_FROM_EMAIL', '').strip()


def _sendgrid_api_key():
    return getattr(settings, 'SENDGRID_API_KEY', '').strip()


def _require_sendgrid_configured():
    if not _sendgrid_api_key():
        raise SendGridConfigurationError('SENDGRID_API_KEY must be configured for email delivery.')
    if not _from_email():
        raise SendGridConfigurationError('SENDGRID_FROM_EMAIL must be configured for email delivery.')


def _send_via_sendgrid(subject, message, recipient_list):
    _require_sendgrid_configured()
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
    """Send a plain-text email through SendGrid only."""
    recipients = [email for email in recipient_list if email]
    if not recipients:
        raise SendGridConfigurationError('At least one recipient email is required for SendGrid delivery.')

    return _send_via_sendgrid(subject, message, recipients)


def _web_password_reset_base_url():
    reset_base_url = getattr(settings, 'FRONTEND_PASSWORD_RESET_URL', '') or 'http://localhost:5173/reset-password'
    parsed_url = urlsplit(reset_base_url)
    normalized_path = parsed_url.path.rstrip('/')
    if normalized_path.endswith('/forgot-password'):
        reset_path = f'{normalized_path.removesuffix("/forgot-password")}/reset-password'
        return urlunsplit((parsed_url.scheme, parsed_url.netloc, reset_path, '', ''))
    return reset_base_url


def build_password_reset_link(user, otp_code, client_app='mobile'):
    if client_app == 'web':
        reset_base_url = _web_password_reset_base_url()
    else:
        reset_base_url = getattr(settings, 'MOBILE_PASSWORD_RESET_URL', '') or 'http://localhost:5173/forgot-password'
    query_param = 'token' if client_app == 'web' else 'otp'
    separator = '&' if '?' in reset_base_url else '?'
    return f'{reset_base_url}{separator}{urlencode({"email": user.email, query_param: otp_code})}'


def send_password_reset_otp_email(user, otp_code, client_app='mobile'):
    reset_link = build_password_reset_link(user, otp_code, client_app)

    if client_app == 'web':
        message = (
            f'Hello {user.full_name},\n\n'
            'Use the secure link below to reset your HRRecruit password:\n'
            f'{reset_link}\n\n'
            'This reset link expires in 10 minutes. If you did not request a password reset, you can ignore this email.'
        )
    else:
        message = (
            f'Hello {user.full_name},\n\n'
            'Use the OTP below to reset your HRRecruit password in the mobile app:\n'
            f'{otp_code}\n\n'
            'This OTP expires in 10 minutes.'
        )

    return send_email(
        subject='HRRecruit Password Reset',
        message=message,
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


def send_job_offer_email(offer):
    application = offer.application
    salary_amount = getattr(offer, 'salary_amount', None)
    salary_currency = getattr(offer, 'salary_currency', 'MYR')
    start_date = getattr(offer, 'start_date', None) or 'To be confirmed'
    work_arrangement = getattr(offer, 'work_arrangement', '') or 'To be confirmed'
    compensation = f'{salary_currency} {salary_amount}' if salary_amount is not None else 'Not specified'
    return send_email(
        subject=f'Job offer for {application.job.title}',
        message=(
            f'Hello {application.applicant.full_name},\n\n'
            f'You received a job offer for {application.job.title}.\n'
            f'Compensation: {compensation}\n'
            f'Start date: {start_date}\n'
            f'Work arrangement: {work_arrangement}\n'
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
