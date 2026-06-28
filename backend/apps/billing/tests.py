from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.jobs.models import JobPosting
from apps.notifications.models import Notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import Payment, Subscription, SubscriptionPlan
from .services import send_subscription_reminders


class BillingAPITests(APITestCase):
    def setUp(self):
        self.hr_head = User.objects.create_user(
            email='head@example.com', password='StrongPass123!', full_name='HR Head', role=User.Role.HR_HEAD
        )
        self.recruiter = User.objects.create_user(
            email='recruiter@example.com', password='StrongPass123!', full_name='Recruiter', role=User.Role.RECRUITER
        )
        self.organization = Organization.objects.create(
            name='Example Organization',
            registration_no='REG-001',
            email='org@example.com',
            contact_number='+60123456789',
            address='Example address',
            status=Organization.Status.ACTIVE,
            created_by=self.hr_head,
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.hr_head,
            role=OrganizationMembership.Role.HR_HEAD,
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.recruiter,
            role=OrganizationMembership.Role.RECRUITER,
        )
        self.basic_plan, _ = SubscriptionPlan.objects.update_or_create(
            name=SubscriptionPlan.Name.BASIC,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            defaults={
                'max_job_postings': 1,
                'price': '49.00',
                'features_description': 'Test Basic plan',
                'is_active': True,
            },
        )
        self.pro_plan, _ = SubscriptionPlan.objects.update_or_create(
            name=SubscriptionPlan.Name.PRO,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            defaults={
                'max_job_postings': 2,
                'price': '149.00',
                'features_description': 'Test Pro plan',
                'is_active': True,
            },
        )
        self.basic_plan.refresh_from_db()
        self.pro_plan.refresh_from_db()
        self.job_payload = {
            'title': 'Backend Engineer',
            'description': 'Build recruitment APIs with Django.',
            'employment_type': 'full_time',
            'approximate_salary': '7000.00',
            'location': 'Kuala Lumpur',
            'status': JobPosting.Status.OPEN,
        }

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def test_hr_head_can_subscribe_complete_demo_payment_and_view_invoice_history(self):
        self.authenticate(self.hr_head)

        plans_response = self.client.get(reverse('billing-plan-list'))
        subscribe_response = self.client.post(
            reverse('billing-subscribe'), {'plan_id': self.basic_plan.id}, format='json'
        )
        subscription_id = subscribe_response.data['subscription']['id']
        payment_response = self.client.post(
            reverse('billing-demo-payment-success'),
            {'subscription_id': subscription_id, 'transaction_reference': 'DEMO-123'},
            format='json',
        )
        current_response = self.client.get(reverse('billing-current-subscription'))
        invoice_response = self.client.get(reverse('billing-invoice-list'))

        self.assertEqual(plans_response.status_code, status.HTTP_200_OK)
        self.assertEqual(subscribe_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payment_response.data['subscription']['status'], Subscription.Status.ACTIVE)
        self.assertTrue(payment_response.data['payment']['invoice_number'].startswith('INV-'))
        self.assertEqual(payment_response.data['payment']['billing_reason'], Payment.BillingReason.SUBSCRIPTION_CREATE)
        self.assertIsNotNone(payment_response.data['payment']['due_at'])
        self.assertEqual(current_response.status_code, status.HTTP_200_OK)
        self.assertEqual(current_response.data['id'], subscription_id)
        self.assertEqual(invoice_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(invoice_response.data), 1)
        self.assertEqual(Payment.objects.get().status, Payment.Status.PAID)

    def test_hr_head_can_schedule_and_resume_subscription_cancellation(self):
        self.authenticate(self.hr_head)
        subscription = Subscription.objects.create(
            organization=self.organization,
            plan=self.pro_plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
            status=Subscription.Status.ACTIVE,
            is_auto_renew=True,
        )

        cancel_response = self.client.post(
            reverse('billing-subscription-cancel'),
            {'reason': 'Hiring pause for next quarter'},
            format='json',
        )
        subscription.refresh_from_db()

        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertTrue(subscription.cancel_at_period_end)
        self.assertFalse(subscription.is_auto_renew)
        self.assertIsNotNone(subscription.cancelled_at)
        self.assertEqual(subscription.cancellation_reason, 'Hiring pause for next quarter')
        self.assertTrue(cancel_response.data['subscription']['cancel_at_period_end'])

        reactivate_response = self.client.post(reverse('billing-subscription-reactivate'), format='json')
        subscription.refresh_from_db()

        self.assertEqual(reactivate_response.status_code, status.HTTP_200_OK)
        self.assertFalse(subscription.cancel_at_period_end)
        self.assertTrue(subscription.is_auto_renew)
        self.assertIsNone(subscription.cancelled_at)
        self.assertEqual(subscription.cancellation_reason, '')
        self.assertFalse(reactivate_response.data['subscription']['cancel_at_period_end'])

    def test_only_hr_head_can_manage_billing(self):
        self.authenticate(self.recruiter)

        response = self.client.post(reverse('billing-subscribe'), {'plan_id': self.basic_plan.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_active_subscription_limit_blocks_extra_open_job_creation(self):
        Subscription.objects.create(
            organization=self.organization,
            plan=self.basic_plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
            status=Subscription.Status.ACTIVE,
        )
        self.authenticate(self.recruiter)

        first_response = self.client.post(reverse('job-list-create'), self.job_payload, format='json')
        second_response = self.client.post(
            reverse('job-list-create'), {**self.job_payload, 'title': 'Second Backend Engineer'}, format='json'
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('maximum of 1 open job', second_response.data['status'][0])

    @patch('apps.billing.services.send_subscription_reminder_email')
    def test_subscription_reminder_keeps_database_notification_and_mocks_email(self, mock_send_email):
        Subscription.objects.create(
            organization=self.organization,
            plan=self.pro_plan,
            start_date=timezone.localdate() - timedelta(days=23),
            end_date=timezone.localdate() + timedelta(days=7),
            status=Subscription.Status.ACTIVE,
        )

        sent_count = send_subscription_reminders(days_before_end=7)

        self.assertEqual(sent_count, 1)
        mock_send_email.assert_called_once()
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.hr_head,
                notification_type='subscription_reminder',
                title='Subscription reminder',
            ).exists()
        )


class FakeStripeSession:
    id = 'cs_test_123'
    url = 'https://checkout.stripe.test/session/cs_test_123'


class FakeStripeCheckoutSession:
    create_calls = []

    @classmethod
    def create(cls, **kwargs):
        cls.create_calls.append(kwargs)
        return FakeStripeSession()


class FakeStripeWebhook:
    event = None
    error = None

    @classmethod
    def construct_event(cls, payload, signature, secret):
        if cls.error:
            raise cls.error
        return cls.event


class FakeStripeErrorNamespace:
    class SignatureVerificationError(Exception):
        pass


class FakeStripeModule:
    api_key = ''

    class checkout:
        Session = FakeStripeCheckoutSession

    Webhook = FakeStripeWebhook
    error = FakeStripeErrorNamespace


class PaymentGatewayTests(BillingAPITests):
    def setUp(self):
        super().setUp()
        FakeStripeCheckoutSession.create_calls = []
        FakeStripeWebhook.event = None
        FakeStripeWebhook.error = None
        FakeStripeModule.api_key = ''

    def create_pending_subscription(self):
        return Subscription.objects.create(
            organization=self.organization,
            plan=self.pro_plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
            status=Subscription.Status.PENDING,
        )

    @patch('apps.billing.payment_gateways.StripeSandboxGateway._load_stripe', return_value=FakeStripeModule)
    def test_stripe_sandbox_checkout_session_uses_env_keys_and_does_not_call_real_gateway(self, mock_load_stripe):
        self.authenticate(self.hr_head)
        subscription = self.create_pending_subscription()

        with self.settings(
            STRIPE_SECRET_KEY='sk_test_mocked',
            STRIPE_CHECKOUT_SUCCESS_URL='https://frontend.test/billing/success?session_id={CHECKOUT_SESSION_ID}',
            STRIPE_CHECKOUT_CANCEL_URL='https://frontend.test/billing/cancelled',
            STRIPE_CURRENCY='MYR',
        ):
            response = self.client.post(
                reverse('billing-checkout-session'),
                {'subscription_id': subscription.id, 'gateway': Payment.PaymentGateway.STRIPE},
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['gateway'], Payment.PaymentGateway.STRIPE)
        self.assertEqual(response.data['mode'], 'stripe_sandbox')
        self.assertEqual(response.data['checkout_session_id'], 'cs_test_123')
        self.assertEqual(response.data['checkout_url'], 'https://checkout.stripe.test/session/cs_test_123')
        self.assertEqual(FakeStripeModule.api_key, 'sk_test_mocked')
        self.assertEqual(len(FakeStripeCheckoutSession.create_calls), 1)
        create_call = FakeStripeCheckoutSession.create_calls[0]
        self.assertEqual(create_call['mode'], 'payment')
        self.assertEqual(create_call['metadata']['subscription_id'], str(subscription.id))
        self.assertEqual(create_call['line_items'][0]['price_data']['unit_amount'], 14900)
        mock_load_stripe.assert_called_once()
        self.assertFalse(Payment.objects.exists())

    @patch('apps.billing.payment_gateways.StripeSandboxGateway._load_stripe', return_value=FakeStripeModule)
    def test_verified_stripe_webhook_creates_payment_and_activates_subscription(self, mock_load_stripe):
        subscription = self.create_pending_subscription()
        FakeStripeWebhook.event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_paid_123',
                    'payment_status': 'paid',
                    'amount_total': 14900,
                    'currency': 'myr',
                    'metadata': {'subscription_id': str(subscription.id)},
                }
            },
        }

        with self.settings(STRIPE_WEBHOOK_SECRET='whsec_mocked', STRIPE_CURRENCY='MYR'):
            response = self.client.post(
                reverse('billing-stripe-webhook'),
                data=b'{"id":"evt_test"}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=123,v1=mocked',
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['processed'])
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        payment = Payment.objects.get()
        self.assertEqual(payment.payment_gateway, Payment.PaymentGateway.STRIPE)
        self.assertEqual(payment.transaction_reference, 'cs_test_paid_123')
        self.assertEqual(payment.amount, self.pro_plan.price)
        self.assertEqual(payment.currency, 'MYR')
        self.assertEqual(payment.status, Payment.Status.PAID)
        mock_load_stripe.assert_called_once()

    @patch('apps.billing.payment_gateways.StripeSandboxGateway._load_stripe', return_value=FakeStripeModule)
    def test_invalid_stripe_webhook_signature_does_not_create_payment(self, mock_load_stripe):
        self.create_pending_subscription()
        FakeStripeWebhook.error = FakeStripeErrorNamespace.SignatureVerificationError('bad signature')

        with self.settings(STRIPE_WEBHOOK_SECRET='whsec_mocked'):
            response = self.client.post(
                reverse('billing-stripe-webhook'),
                data=b'{"id":"evt_test"}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='bad',
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Payment.objects.exists())
        self.assertFalse(Subscription.objects.filter(status=Subscription.Status.ACTIVE).exists())
        mock_load_stripe.assert_called_once()

    def test_paypal_and_fpx_checkout_are_safe_placeholders(self):
        self.authenticate(self.hr_head)
        subscription = self.create_pending_subscription()

        paypal_response = self.client.post(
            reverse('billing-checkout-session'),
            {'subscription_id': subscription.id, 'gateway': Payment.PaymentGateway.PAYPAL},
            format='json',
        )
        fpx_response = self.client.post(
            reverse('billing-checkout-session'),
            {'subscription_id': subscription.id, 'gateway': Payment.PaymentGateway.FPX},
            format='json',
        )

        self.assertEqual(paypal_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(fpx_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not supported', paypal_response.data['detail'])
        self.assertIn('not supported', fpx_response.data['detail'])
        self.assertFalse(Payment.objects.exists())
