from django.db import models
from django.utils import timezone

from apps.organizations.models import Organization


class SubscriptionPlan(models.Model):
    class Name(models.TextChoices):
        BASIC = 'Basic', 'Basic'
        PRO = 'Pro', 'Pro'
        ENTERPRISE = 'Enterprise', 'Enterprise'

    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    name = models.CharField(max_length=50, choices=Name.choices)
    max_job_postings = models.PositiveIntegerField()
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features_description = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['price', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'billing_cycle'],
                name='unique_subscription_plan_name_cycle',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_billing_cycle_display()})'


class Subscription(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return f'{self.organization.name} - {self.plan.name} ({self.status})'


class Payment(models.Model):
    class PaymentGateway(models.TextChoices):
        DEMO = 'demo', 'Demo'
        STRIPE = 'stripe', 'Stripe'
        PAYPAL = 'paypal', 'PayPal'
        FPX = 'fpx', 'FPX'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    payment_gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices,
        default=PaymentGateway.DEMO,
    )
    transaction_reference = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='MYR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(blank=True, null=True)
    invoice_number = models.CharField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ['-paid_at', '-id']
        indexes = [
            models.Index(fields=['payment_gateway', 'status']),
            models.Index(fields=['invoice_number']),
        ]

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            super().save(*args, **kwargs)
            self.invoice_number = f'INV-{timezone.now():%Y%m%d}-{self.id:06d}'
            return super().save(update_fields=['invoice_number'])
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.invoice_number} - {self.amount} {self.currency} ({self.status})'
