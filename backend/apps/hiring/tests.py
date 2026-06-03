from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.hiring.models import HiringDecision, JobOffer
from apps.jobs.models import JobPosting
from apps.notifications.models import Notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


class HiringWorkflowAPITests(APITestCase):
    def setUp(self):
        self.hr_head = self.create_user('head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('recruiter@example.com', User.Role.RECRUITER)
        self.applicant = self.create_user('applicant@example.com', User.Role.APPLICANT)
        self.other_head = self.create_user('other-head@example.com', User.Role.HR_HEAD)
        self.other_recruiter = self.create_user('other-recruiter@example.com', User.Role.RECRUITER)
        self.organization = self.create_organization('Example Organization', self.hr_head, 'REG-HIRE')
        self.other_organization = self.create_organization('Other Organization', self.other_head, 'REG-OTHER-HIRE')
        self.create_membership(self.hr_head, self.organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.create_membership(self.other_head, self.other_organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.other_recruiter, self.other_organization, OrganizationMembership.Role.RECRUITER)
        self.job = self.create_job(self.recruiter, self.organization)
        self.application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            status=JobApplication.Status.EVALUATION_SUBMITTED,
        )

    def create_user(self, email, role):
        return User.objects.create_user(email=email, password='test-pass-123', full_name=email, role=role)

    def create_organization(self, name, hr_head, registration_no):
        return Organization.objects.create(
            name=name,
            registration_no=registration_no,
            email=f'{registration_no.lower()}@example.com',
            contact_number='+60123456789',
            address='Example address',
            status=Organization.Status.ACTIVE,
            created_by=hr_head,
        )

    def create_membership(self, user, organization, role):
        return OrganizationMembership.objects.create(organization=organization, user=user, role=role)

    def create_job(self, recruiter, organization):
        return JobPosting.objects.create(
            organization=organization,
            recruiter=recruiter,
            title='Backend Engineer',
            description='Build APIs',
            employment_type='Full-time',
            approximate_salary='5000.00',
            location='Kuala Lumpur',
            status=JobPosting.Status.OPEN,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def submit_hire_decision(self):
        self.authenticate(self.recruiter)
        return self.client.post(
            reverse('application-hiring-decision', args=[self.application.id]),
            {'decision': HiringDecision.Decision.HIRE, 'justification': 'Strong evaluation and role fit.'},
            format='json',
        )

    def approve_decision(self, decision):
        self.authenticate(self.hr_head)
        return self.client.post(
            reverse('hiring-decision-approve', args=[decision.id]),
            {'justification': 'Approved within headcount plan.'},
            format='json',
        )

    def send_offer(self):
        self.authenticate(self.recruiter)
        return self.client.post(
            reverse('application-job-offer', args=[self.application.id]),
            {
                'offer_message': 'We are pleased to offer you the Backend Engineer role.',
                'respond_deadline': (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            },
            format='json',
        )

    def test_recruiter_to_hr_head_to_applicant_hire_offer_flow(self):
        submit_response = self.submit_hire_decision()
        self.assertEqual(submit_response.status_code, status.HTTP_201_CREATED)
        decision = HiringDecision.objects.get(application=self.application)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.DECISION_PENDING)
        self.assertTrue(Notification.objects.filter(recipient=self.hr_head, title='Hiring decision pending approval').exists())

        self.authenticate(self.hr_head)
        pending_response = self.client.get(reverse('hiring-decision-pending-list'))
        self.assertEqual(pending_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in pending_response.data], [decision.id])

        approve_response = self.approve_decision(decision)
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        decision.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(decision.status, HiringDecision.Status.APPROVED)
        self.assertEqual(decision.hr_head, self.hr_head)
        self.assertEqual(self.application.status, JobApplication.Status.HR_APPROVED)
        self.assertTrue(Notification.objects.filter(recipient=self.recruiter, title='Hiring decision approved').exists())

        offer_response = self.send_offer()
        self.assertEqual(offer_response.status_code, status.HTTP_201_CREATED)
        offer = JobOffer.objects.get(application=self.application)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.OFFER_SENT)
        self.assertTrue(Notification.objects.filter(recipient=self.applicant, title='Job offer received').exists())

        self.authenticate(self.applicant)
        offer_list_response = self.client.get(reverse('job-offer-list'))
        accept_response = self.client.post(reverse('job-offer-accept', args=[offer.id]), {}, format='json')
        self.assertEqual(offer_list_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in offer_list_response.data], [offer.id])
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        offer.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(offer.offer_status, JobOffer.OfferStatus.ACCEPTED)
        self.assertEqual(self.application.status, JobApplication.Status.OFFER_ACCEPTED)
        self.assertTrue(Notification.objects.filter(recipient=self.recruiter, title='Job offer accepted').exists())
        self.assertEqual(ApplicationStageHistory.objects.filter(application=self.application).count(), 4)

    def test_hr_head_rejects_hiring_decision_and_records_status_history(self):
        self.submit_hire_decision()
        decision = HiringDecision.objects.get(application=self.application)
        self.authenticate(self.hr_head)

        response = self.client.post(
            reverse('hiring-decision-reject', args=[decision.id]),
            {'justification': 'Compensation band is not approved.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        decision.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(decision.status, HiringDecision.Status.REJECTED)
        self.assertEqual(self.application.status, JobApplication.Status.HR_REJECTED)
        latest_history = self.application.stage_history.first()
        self.assertEqual(latest_history.to_stage, JobApplication.Status.HR_REJECTED)
        self.assertIn('Compensation band is not approved.', latest_history.note)

    def test_hr_approved_reject_decision_notifies_applicant_and_rejects_application(self):
        self.authenticate(self.recruiter)
        submit_response = self.client.post(
            reverse('application-hiring-decision', args=[self.application.id]),
            {'decision': HiringDecision.Decision.REJECT, 'justification': 'Evaluation did not meet bar.'},
            format='json',
        )
        decision = HiringDecision.objects.get(id=submit_response.data['id'])

        response = self.approve_decision(decision)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.REJECTED)
        self.assertTrue(Notification.objects.filter(recipient=self.applicant, title='Application status updated').exists())

    def test_organization_isolation_for_pending_decisions_and_offers(self):
        self.submit_hire_decision()
        decision = HiringDecision.objects.get(application=self.application)
        self.authenticate(self.other_head)

        pending_response = self.client.get(reverse('hiring-decision-pending-list'))
        detail_response = self.client.get(reverse('hiring-decision-detail', args=[decision.id]))

        self.assertEqual(pending_response.status_code, status.HTTP_200_OK)
        self.assertEqual(pending_response.data, [])
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_job_offer_requires_hr_approved_hire_decision(self):
        self.authenticate(self.recruiter)

        response = self.client.post(
            reverse('application-job-offer', args=[self.application.id]),
            {
                'offer_message': 'Offer before approval.',
                'respond_deadline': (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(JobOffer.objects.count(), 0)

    def test_applicant_declines_job_offer(self):
        self.submit_hire_decision()
        decision = HiringDecision.objects.get(application=self.application)
        self.approve_decision(decision)
        self.send_offer()
        offer = JobOffer.objects.get(application=self.application)
        self.authenticate(self.applicant)

        response = self.client.post(
            reverse('job-offer-decline', args=[offer.id]),
            {'reason': 'Accepted another opportunity.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        offer.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(offer.offer_status, JobOffer.OfferStatus.DECLINED)
        self.assertEqual(self.application.status, JobApplication.Status.OFFER_DECLINED)
        self.assertTrue(Notification.objects.filter(recipient=self.recruiter, title='Job offer declined').exists())
