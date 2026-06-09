"""Service helpers for organization and team setup."""

import secrets
import string

from django.db import transaction
from rest_framework import serializers

from apps.notifications.email_service import send_team_account_created_email
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
    """Send credentials through the notification email service."""
    send_team_account_created_email(user, temporary_password)


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
