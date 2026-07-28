"""Business helpers for billing and subscription enforcement."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.notifications.email_service import send_subscription_reminder_email
from apps.notifications.services import create_notification
from apps.organizations.models import Organization, OrganizationMembership

from .models import Payment, Subscription


class SubscriptionLimitError(APIException):
    """Raised when an organization exceeds its subscription limits."""

    status_code = 400

    def __init__(self, detail, *, limit_type=None, current_usage=None, limit=None, plan=None):
        APIException.__init__(self, detail)
        self.detail = detail
        self.limit_type = limit_type
        self.current_usage = current_usage
        self.limit = limit
        self.plan = plan

    def as_dict(self):
        return {key: value for key, value in {
            'detail': self.detail, 'limit_type': self.limit_type,
            'current_usage': self.current_usage, 'limit': self.limit, 'plan': self.plan,
        }.items() if value is not None}


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
    validate_target_plan_capacity(organization, plan)
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

    Organization.objects.select_for_update().get(pk=subscription.organization_id)
    subscription.refresh_from_db()
    validate_target_plan_capacity(subscription.organization, subscription.plan)
    Subscription.objects.filter(
        organization=subscription.organization,
        status=Subscription.Status.ACTIVE,
    ).exclude(id=subscription.id).update(status=Subscription.Status.CANCELLED)
    subscription.status = Subscription.Status.ACTIVE
    subscription.cancel_at_period_end = False
    subscription.cancelled_at = None
    subscription.cancellation_reason = ''
    subscription.save(
        update_fields=[
            'status',
            'cancel_at_period_end',
            'cancelled_at',
            'cancellation_reason',
        ]
    )
    return Payment.objects.create(
        subscription=subscription,
        payment_gateway=gateway,
        transaction_reference=transaction_reference,
        amount=amount if amount is not None else subscription.plan.price,
        currency=currency,
        status=Payment.Status.PAID,
        billing_reason=Payment.BillingReason.SUBSCRIPTION_CREATE,
        paid_at=timezone.now(),
        due_at=timezone.now(),
    )


def cancel_subscription_at_period_end(subscription, reason=''):
    if subscription.status != Subscription.Status.ACTIVE:
        raise ValidationError('Only active subscriptions can be scheduled for cancellation.')
    subscription.cancel_at_period_end = True
    subscription.cancelled_at = timezone.now()
    subscription.cancellation_reason = reason or ''
    subscription.is_auto_renew = False
    subscription.save(
        update_fields=[
            'cancel_at_period_end',
            'cancelled_at',
            'cancellation_reason',
            'is_auto_renew',
        ]
    )
    return subscription


def reactivate_subscription(subscription):
    if subscription.status != Subscription.Status.ACTIVE:
        raise ValidationError('Only active subscriptions can be resumed.')
    subscription.cancel_at_period_end = False
    subscription.cancelled_at = None
    subscription.cancellation_reason = ''
    subscription.is_auto_renew = True
    subscription.save(
        update_fields=[
            'cancel_at_period_end',
            'cancelled_at',
            'cancellation_reason',
            'is_auto_renew',
        ]
    )
    return subscription


def activate_demo_subscription(subscription, transaction_reference=''):
    return activate_paid_subscription(
        subscription=subscription,
        gateway=Payment.PaymentGateway.DEMO,
        transaction_reference=transaction_reference,
        amount=subscription.plan.price,
        currency='MYR',
    )


def get_subscription_usage(organization):
    from apps.jobs.models import JobPosting
    memberships = OrganizationMembership.objects.filter(
        organization=organization, status=OrganizationMembership.Status.ACTIVE, user__is_active=True,
    )
    return {
        'hiring_managers': memberships.filter(role=OrganizationMembership.Role.HR_HEAD).count(),
        'recruiters': memberships.filter(role=OrganizationMembership.Role.RECRUITER).count(),
        'interviewers': memberships.filter(role=OrganizationMembership.Role.INTERVIEWER).count(),
        'active_job_postings': JobPosting.objects.filter(
            organization=organization, status=JobPosting.Status.OPEN,
        ).count(),
    }


LIMIT_FIELDS = {
    'hiring_managers': 'max_hiring_managers', 'recruiters': 'max_recruiters',
    'interviewers': 'max_interviewers', 'active_job_postings': 'max_active_job_postings',
}
ROLE_LIMIT_TYPES = {
    OrganizationMembership.Role.HR_HEAD: 'hiring_managers',
    OrganizationMembership.Role.RECRUITER: 'recruiters',
    OrganizationMembership.Role.INTERVIEWER: 'interviewers',
}


def get_subscription_capacity(organization):
    subscription = get_active_subscription(organization)
    if not subscription:
        return None
    usage = get_subscription_usage(organization)
    return {'plan': subscription.plan.name, 'usage': {
        key: {'used': used, 'limit': getattr(subscription.plan, LIMIT_FIELDS[key]),
              'remaining': max(getattr(subscription.plan, LIMIT_FIELDS[key]) - used, 0)}
        for key, used in usage.items()
    }}


def validate_target_plan_capacity(organization, plan):
    usage = get_subscription_usage(organization)
    exceeded = [
        {
            'limit_type': key,
            'current_usage': usage[key],
            'limit': getattr(plan, field),
        }
        for key, field in LIMIT_FIELDS.items()
        if usage[key] > getattr(plan, field)
    ]
    if exceeded:
        error = SubscriptionLimitError('Current organization usage exceeds the selected plan.')
        error.exceeded_limits = exceeded
        error.detail = {'detail': 'Current organization usage exceeds the selected plan.', 'exceeded_limits': exceeded}
        raise error


def enforce_member_limit(organization, role):
    subscription = get_active_subscription(organization)
    if not subscription:
        raise SubscriptionLimitError('An active subscription is required before creating organization team accounts.')
    limit_type = ROLE_LIMIT_TYPES[role]
    used = get_subscription_usage(organization)[limit_type]
    limit = getattr(subscription.plan, LIMIT_FIELDS[limit_type])
    if used >= limit:
        label = OrganizationMembership.Role(role).label
        raise SubscriptionLimitError(
            f'Your {subscription.plan.name} plan allows a maximum of {limit} active {label} account(s).',
            limit_type=limit_type, current_usage=used, limit=limit, plan=subscription.plan.name,
        )


def enforce_open_job_limit(organization, open_job_count=None, excluding_job=None):
    subscription = get_active_subscription(organization)
    if not subscription:
        raise SubscriptionLimitError('An active subscription is required before opening job postings.')
    max_open_jobs = subscription.plan.max_active_job_postings
    if open_job_count is None:
        open_job_count = get_subscription_usage(organization)['active_job_postings']
    if open_job_count >= max_open_jobs:
        raise SubscriptionLimitError(
            f'Your {subscription.plan.name} plan allows a maximum of {max_open_jobs} active job postings. Close an active job or ask a Hiring Manager to upgrade the subscription.',
            limit_type='active_job_postings', current_usage=open_job_count,
            limit=max_open_jobs, plan=subscription.plan.name,
        )


def send_subscription_reminders(days_before_end=7):
    """Notify hiring managers when active subscriptions are approaching their end date."""
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
