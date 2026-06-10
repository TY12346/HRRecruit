"""Payment gateway abstraction for demo and optional real billing providers."""

from decimal import Decimal
from importlib import import_module

from django.conf import settings
from django.urls import reverse
from rest_framework.exceptions import APIException

from .models import Payment, Subscription
from .services import activate_paid_subscription


class PaymentGatewayError(APIException):
    status_code = 400
    default_detail = 'Payment gateway request could not be completed.'
    default_code = 'payment_gateway_error'


class PaymentGatewayNotConfigured(PaymentGatewayError):
    default_detail = 'Payment gateway is not configured.'
    default_code = 'payment_gateway_not_configured'


class PaymentGatewayUnsupported(PaymentGatewayError):
    default_detail = 'Payment gateway is not supported yet.'
    default_code = 'payment_gateway_unsupported'


class BasePaymentGateway:
    gateway_name = None

    def create_checkout_session(self, subscription, request=None):
        raise PaymentGatewayUnsupported('Checkout sessions are not supported for this gateway.')

    def handle_webhook(self, payload, signature):
        raise PaymentGatewayUnsupported('Webhooks are not supported for this gateway.')


class DemoPaymentGateway(BasePaymentGateway):
    gateway_name = Payment.PaymentGateway.DEMO

    def create_checkout_session(self, subscription, request=None):
        endpoint = reverse('billing-demo-payment-success')
        if request is not None:
            endpoint = request.build_absolute_uri(endpoint)
        return {
            'gateway': self.gateway_name,
            'mode': 'demo',
            'subscription_id': subscription.id,
            'checkout_url': endpoint,
            'message': 'Use the demo payment success endpoint to activate this subscription.',
        }


class StripeSandboxGateway(BasePaymentGateway):
    gateway_name = Payment.PaymentGateway.STRIPE

    def _load_stripe(self):
        return import_module('stripe')

    def _get_secret_key(self):
        secret_key = settings.STRIPE_SECRET_KEY
        if not secret_key:
            raise PaymentGatewayNotConfigured('STRIPE_SECRET_KEY is required for Stripe sandbox checkout.')
        return secret_key

    def _get_webhook_secret(self):
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        if not webhook_secret:
            raise PaymentGatewayNotConfigured('STRIPE_WEBHOOK_SECRET is required to verify Stripe webhooks.')
        return webhook_secret

    def _success_url(self, request):
        if settings.STRIPE_CHECKOUT_SUCCESS_URL:
            return settings.STRIPE_CHECKOUT_SUCCESS_URL
        return request.build_absolute_uri('/billing/success?session_id={CHECKOUT_SESSION_ID}')

    def _cancel_url(self, request):
        if settings.STRIPE_CHECKOUT_CANCEL_URL:
            return settings.STRIPE_CHECKOUT_CANCEL_URL
        return request.build_absolute_uri('/billing/cancelled')

    def _amount_in_minor_units(self, amount):
        return int((Decimal(amount) * Decimal('100')).quantize(Decimal('1')))

    def create_checkout_session(self, subscription, request=None):
        if request is None:
            raise PaymentGatewayError('Request context is required to build Stripe checkout URLs.')
        stripe = self._load_stripe()
        stripe.api_key = self._get_secret_key()
        currency = settings.STRIPE_CURRENCY.lower()
        session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': f'HRRecruit {subscription.plan.name} subscription',
                            'description': subscription.plan.features_description,
                        },
                        'unit_amount': self._amount_in_minor_units(subscription.plan.price),
                    },
                    'quantity': 1,
                }
            ],
            metadata={
                'subscription_id': str(subscription.id),
                'organization_id': str(subscription.organization_id),
                'plan_id': str(subscription.plan_id),
                'gateway': self.gateway_name,
                'environment': 'sandbox',
            },
            success_url=self._success_url(request),
            cancel_url=self._cancel_url(request),
        )
        return {
            'gateway': self.gateway_name,
            'mode': 'stripe_sandbox',
            'subscription_id': subscription.id,
            'checkout_session_id': session.id,
            'checkout_url': session.url,
        }

    def handle_webhook(self, payload, signature):
        stripe = self._load_stripe()
        try:
            event = stripe.Webhook.construct_event(payload, signature, self._get_webhook_secret())
        except ValueError as exc:
            raise PaymentGatewayError('Invalid Stripe webhook payload.') from exc
        except stripe.error.SignatureVerificationError as exc:
            raise PaymentGatewayError('Invalid Stripe webhook signature.') from exc

        if event.get('type') != 'checkout.session.completed':
            return {'processed': False, 'message': 'Stripe event ignored.', 'event_type': event.get('type')}

        session = event['data']['object']
        if session.get('payment_status') != 'paid':
            return {'processed': False, 'message': 'Stripe checkout session is not paid.'}

        subscription_id = session.get('metadata', {}).get('subscription_id')
        if not subscription_id:
            raise PaymentGatewayError('Stripe checkout session metadata is missing subscription_id.')

        try:
            subscription = Subscription.objects.select_related('organization', 'plan').get(
                id=subscription_id,
                status=Subscription.Status.PENDING,
            )
        except Subscription.DoesNotExist as exc:
            existing_payment = Payment.objects.filter(
                payment_gateway=Payment.PaymentGateway.STRIPE,
                transaction_reference=session.get('id', ''),
                status=Payment.Status.PAID,
            ).select_related('subscription').first()
            if existing_payment:
                return {'processed': True, 'payment': existing_payment, 'idempotent': True}
            raise PaymentGatewayError('Pending subscription not found for verified Stripe payment.') from exc

        amount_total = session.get('amount_total')
        amount = Decimal(amount_total) / Decimal('100') if amount_total is not None else subscription.plan.price
        currency = session.get('currency', settings.STRIPE_CURRENCY).upper()
        payment = activate_paid_subscription(
            subscription=subscription,
            gateway=Payment.PaymentGateway.STRIPE,
            transaction_reference=session.get('id', ''),
            amount=amount,
            currency=currency,
        )
        return {'processed': True, 'payment': payment, 'idempotent': False}


class PayPalPlaceholderGateway(BasePaymentGateway):
    gateway_name = Payment.PaymentGateway.PAYPAL


class FPXPlaceholderGateway(BasePaymentGateway):
    gateway_name = Payment.PaymentGateway.FPX


def get_payment_gateway(gateway_name):
    gateways = {
        Payment.PaymentGateway.DEMO: DemoPaymentGateway,
        Payment.PaymentGateway.STRIPE: StripeSandboxGateway,
        Payment.PaymentGateway.PAYPAL: PayPalPlaceholderGateway,
        Payment.PaymentGateway.FPX: FPXPlaceholderGateway,
    }
    gateway_class = gateways.get(gateway_name)
    if not gateway_class:
        raise PaymentGatewayUnsupported('Unknown payment gateway.')
    return gateway_class()
