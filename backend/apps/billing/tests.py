from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import Payment, Subscription, SubscriptionPlan


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
        self.assertEqual(current_response.status_code, status.HTTP_200_OK)
        self.assertEqual(current_response.data['id'], subscription_id)
        self.assertEqual(invoice_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(invoice_response.data), 1)
        self.assertEqual(Payment.objects.get().status, Payment.Status.PAID)

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
