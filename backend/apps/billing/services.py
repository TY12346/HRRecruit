"""Business helpers for demo billing and subscription enforcement."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationMembership

from .models import Payment, Subscription


class SubscriptionLimitError(Exception):
    """Raised when an organization exceeds its subscription limits."""


def get_active_hr_head_membership(user):
    return OrganizationMembership.objects.filter(
        user=user,
        role=OrganizationMembership.Role.HR_HEAD,
        status=OrganizationMembership.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    ).select_related('organization').first()


def get_active_subscription(organization):
    today = timezone.localdate()
    return (
        Subscription.objects.filter(
            organization=organization,
            status=Subscription.Status.ACTIVE,
            start_date__lte=today,
            end_date__gte=today,
        )
        .select_related('plan')
        .order_by('-created_at')
        .first()
    )


def build_subscription_dates(plan):
    today = timezone.localdate()
    duration = timedelta(days=365 if plan.billing_cycle == plan.BillingCycle.YEARLY else 30)
    return today, today + duration


def create_pending_subscription(organization, plan, is_auto_renew=False):
    start_date, end_date = build_subscription_dates(plan)
    return Subscription.objects.create(
        organization=organization,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        status=Subscription.Status.PENDING,
        is_auto_renew=is_auto_renew,
    )


@transaction.atomic
def activate_demo_subscription(subscription, transaction_reference=''):
    Subscription.objects.filter(
        organization=subscription.organization,
        status=Subscription.Status.ACTIVE,
    ).exclude(id=subscription.id).update(status=Subscription.Status.CANCELLED)
    subscription.status = Subscription.Status.ACTIVE
    subscription.save(update_fields=['status'])
    return Payment.objects.create(
        subscription=subscription,
        payment_gateway=Payment.PaymentGateway.DEMO,
        transaction_reference=transaction_reference,
        amount=subscription.plan.price,
        currency='MYR',
        status=Payment.Status.PAID,
        paid_at=timezone.now(),
    )


def enforce_open_job_limit(organization, open_job_count, excluding_job=None):
    subscription = get_active_subscription(organization)
    if not subscription:
        raise SubscriptionLimitError('An active subscription is required before opening job postings.')
    max_open_jobs = subscription.plan.max_job_postings
    if open_job_count >= max_open_jobs:
        raise SubscriptionLimitError(
            f'Your {subscription.plan.name} plan allows a maximum of {max_open_jobs} open job posting(s).'
        )
