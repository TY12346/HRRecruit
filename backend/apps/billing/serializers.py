"""Serializers for subscription and billing APIs."""

from rest_framework import serializers

from .models import Payment, Subscription, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'max_job_postings',
            'billing_cycle',
            'price',
            'features_description',
            'is_active',
        ]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id',
            'organization',
            'organization_name',
            'plan',
            'start_date',
            'end_date',
            'status',
            'is_auto_renew',
            'trial_end_date',
            'cancel_at_period_end',
            'cancelled_at',
            'cancellation_reason',
            'created_at',
        ]
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    plan_name = serializers.CharField(source='subscription.plan.name', read_only=True)
    billing_cycle = serializers.CharField(source='subscription.plan.billing_cycle', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'invoice_number',
            'subscription',
            'plan_name',
            'billing_cycle',
            'payment_gateway',
            'transaction_reference',
            'amount',
            'currency',
            'status',
            'billing_reason',
            'paid_at',
            'due_at',
            'hosted_invoice_url',
            'receipt_url',
            'failure_reason',
        ]
        read_only_fields = fields


class PlanSelectionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    is_auto_renew = serializers.BooleanField(default=False)

    def validate_plan_id(self, value):
        try:
            return SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist as exc:
            raise serializers.ValidationError('Active subscription plan not found.') from exc


class DemoPaymentSuccessSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField()
    transaction_reference = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_subscription_id(self, value):
        organization = self.context['organization']
        try:
            return Subscription.objects.select_related('plan', 'organization').get(
                id=value,
                organization=organization,
                status=Subscription.Status.PENDING,
            )
        except Subscription.DoesNotExist as exc:
            raise serializers.ValidationError('Pending subscription not found for this organization.') from exc


class CheckoutSessionSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField()
    gateway = serializers.ChoiceField(
        choices=[
            Payment.PaymentGateway.DEMO,
            Payment.PaymentGateway.STRIPE,
            Payment.PaymentGateway.PAYPAL,
            Payment.PaymentGateway.FPX,
        ],
        default=Payment.PaymentGateway.DEMO,
    )

    def validate_subscription_id(self, value):
        organization = self.context['organization']
        try:
            return Subscription.objects.select_related('plan', 'organization').get(
                id=value,
                organization=organization,
                status=Subscription.Status.PENDING,
            )
        except Subscription.DoesNotExist as exc:
            raise serializers.ValidationError('Pending subscription not found for this organization.') from exc


class SubscriptionCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, trim_whitespace=True)
