"""Business helpers for billing and subscription enforcement."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.notifications.email_service import send_subscription_reminder_email
from apps.notifications.services import create_notification
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
def activate_paid_subscription(subscription, gateway, transaction_reference='', amount=None, currency='MYR'):
    if transaction_reference:
        existing_payment = Payment.objects.filter(
            payment_gateway=gateway,
            transaction_reference=transaction_reference,
            status=Payment.Status.PAID,
        ).select_related('subscription').first()
        if existing_payment:
            return existing_payment

    Subscription.objects.filter(
        organization=subscription.organization,
        status=Subscription.Status.ACTIVE,
    ).exclude(id=subscription.id).update(status=Subscription.Status.CANCELLED)
    subscription.status = Subscription.Status.ACTIVE
    subscription.save(update_fields=['status'])
    return Payment.objects.create(
        subscription=subscription,
        payment_gateway=gateway,
        transaction_reference=transaction_reference,
        amount=amount if amount is not None else subscription.plan.price,
        currency=currency,
        status=Payment.Status.PAID,
        paid_at=timezone.now(),
    )


def activate_demo_subscription(subscription, transaction_reference=''):
    return activate_paid_subscription(
        subscription=subscription,
        gateway=Payment.PaymentGateway.DEMO,
        transaction_reference=transaction_reference,
        amount=subscription.plan.price,
        currency='MYR',
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


def send_subscription_reminders(days_before_end=7):
    """Notify HR heads when active subscriptions are approaching their end date."""
    target_date = timezone.localdate() + timedelta(days=days_before_end)
    subscriptions = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        end_date=target_date,
    ).select_related('organization', 'plan')
    sent_count = 0
    for subscription in subscriptions:
        hr_heads = OrganizationMembership.objects.filter(
            organization=subscription.organization,
            role=OrganizationMembership.Role.HR_HEAD,
            status=OrganizationMembership.Status.ACTIVE,
            user__is_active=True,
        ).select_related('user')
        for membership in hr_heads:
            create_notification(
                membership.user,
                'subscription_reminder',
                'Subscription reminder',
                f'Your {subscription.plan.name} subscription ends on {subscription.end_date}.',
                related_entity=subscription,
            )
            send_subscription_reminder_email(membership.user, subscription)
            sent_count += 1
    return sent_count
