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


def get_organization_deletion_blockers(organization):
    """Return human-readable reasons that prevent an organization from being deleted."""
    from apps.applications.models import JobApplication
    from apps.billing.models import Payment, Subscription
    from apps.hiring.models import HiringDecision, JobOffer
    from apps.interviews.models import Interview
    from apps.jobs.models import JobPosting

    blockers = []

    active_job_count = organization.job_postings.exclude(status=JobPosting.Status.CLOSED).count()
    if active_job_count:
        blockers.append('Close all draft or open job postings before deleting the organization.')

    active_application_statuses = [
        JobApplication.Status.SUBMITTED,
        JobApplication.Status.SCREENED,
        JobApplication.Status.SCREENED_QUALIFIED,
        JobApplication.Status.SCREENED_NOT_QUALIFIED,
        JobApplication.Status.SHORTLISTED,
        JobApplication.Status.INTERVIEW_INVITED,
        JobApplication.Status.INTERVIEW_ACCEPTED,
        JobApplication.Status.INTERVIEWING,
        JobApplication.Status.EVALUATION_SUBMITTED,
        JobApplication.Status.DECISION_PENDING,
        JobApplication.Status.HR_APPROVED,
        JobApplication.Status.OFFER_SENT,
        JobApplication.Status.OFFER_ACCEPTED,
    ]
    active_application_count = JobApplication.objects.filter(
        job__organization=organization,
        status__in=active_application_statuses,
    ).count()
    if active_application_count:
        blockers.append('Resolve all active job applications before deleting the organization.')

    active_interview_count = organization.interviews.filter(
        status__in=[
            Interview.Status.ASSIGNED,
            Interview.Status.SCHEDULED,
        ],
    ).count()
    if active_interview_count:
        blockers.append('Complete, cancel, or decline all active interviews before deleting the organization.')

    pending_decision_count = HiringDecision.objects.filter(
        application__job__organization=organization,
        status=HiringDecision.Status.PENDING_HR_APPROVAL,
    ).count()
    if pending_decision_count:
        blockers.append('Approve or reject all pending hiring decisions before deleting the organization.')

    sent_offer_count = JobOffer.objects.filter(
        application__job__organization=organization,
        offer_status=JobOffer.OfferStatus.SENT,
    ).count()
    if sent_offer_count:
        blockers.append('Wait for sent job offers to be accepted, declined, or expired before deleting the organization.')

    active_subscription_count = organization.subscriptions.filter(
        status__in=[Subscription.Status.PENDING, Subscription.Status.ACTIVE],
    ).count()
    if active_subscription_count:
        blockers.append('Cancel or let active subscriptions expire before deleting the organization.')

    pending_payment_count = Payment.objects.filter(
        subscription__organization=organization,
        status=Payment.Status.PENDING,
    ).count()
    if pending_payment_count:
        blockers.append('Resolve pending payments before deleting the organization.')

    return blockers


@transaction.atomic
def delete_organization_account(organization):
    """Soft-delete an organization account after business validations pass."""
    blockers = get_organization_deletion_blockers(organization)
    if blockers:
        raise serializers.ValidationError({'detail': 'Organization cannot be deleted yet.', 'blockers': blockers})

    organization.status = Organization.Status.DELETED
    organization.save(update_fields=['status', 'updated_at'])
    organization.memberships.update(status=OrganizationMembership.Status.INACTIVE)
    User.objects.filter(
        organization_memberships__organization=organization,
        organization_memberships__role__in=[OrganizationMembership.Role.RECRUITER, OrganizationMembership.Role.INTERVIEWER],
    ).update(is_active=False)
    return organization
