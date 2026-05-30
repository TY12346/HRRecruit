"""Service helpers for organization and team setup."""

import secrets
import string

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import serializers

from apps.users.models import User

from .models import Organization, OrganizationMembership


def verify_company_registration(registration_no):
    """Mock company-registration verification until a real provider is selected."""
    return bool(registration_no.strip())


def generate_temporary_password(length=14):
    """Generate a temporary password containing each common character group."""
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice('!@#$%'),
    ]
    password_characters = required + [secrets.choice(alphabet) for _ in range(length - len(required))]
    secrets.SystemRandom().shuffle(password_characters)
    return ''.join(password_characters)


def send_temporary_password_email(user, temporary_password):
    """Send credentials through Django's configured backend (console locally)."""
    send_mail(
        subject='Your HRRecruit team account',
        message=(
            f'Hello {user.full_name},\n\n'
            'An HRRecruit team account has been created for you.\n'
            f'Email: {user.email}\n'
            f'Temporary password: {temporary_password}\n\n'
            'Please log in and change your password.'
        ),
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@hrrecruit.local'),
        recipient_list=[user.email],
    )


@transaction.atomic
def create_team_member(*, organization, email, full_name, phone_number='', role):
    """Create a recruiter or interviewer, attach them to an organization, and email credentials."""
    if role not in (User.Role.RECRUITER, User.Role.INTERVIEWER):
        raise serializers.ValidationError({'role': 'Only recruiter and interviewer accounts can be created.'})

    normalized_email = User.objects.normalize_email(email)
    if User.objects.filter(email__iexact=normalized_email).exists():
        raise serializers.ValidationError({'email': 'A user with this email already exists.'})

    temporary_password = generate_temporary_password()
    user = User.objects.create_user(
        email=normalized_email,
        password=temporary_password,
        full_name=full_name,
        phone_number=phone_number,
        role=role,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=role,
    )
    send_temporary_password_email(user, temporary_password)
    return user
