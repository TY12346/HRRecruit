from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import ApplicationStageHistory, JobApplication


class JobApplicationAPITests(APITestCase):
    def setUp(self):
        self.hr_head = self.create_user('head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('recruiter@example.com', User.Role.RECRUITER)
        self.other_recruiter = self.create_user('other-recruiter@example.com', User.Role.RECRUITER)
        self.applicant = self.create_user('applicant@example.com', User.Role.APPLICANT)
        self.other_applicant = self.create_user('other-applicant@example.com', User.Role.APPLICANT)
        self.organization = self.create_organization('Example Organization', self.hr_head)
        self.create_membership(self.hr_head, self.organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.create_membership(self.other_recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.job = self.create_job(self.recruiter)

    def create_user(self, email, role):
        return User.objects.create_user(email=email, password='test-pass-123', full_name=email, role=role)

    def create_organization(self, name, hr_head):
        return Organization.objects.create(
            name=name,
            registration_no=f'REG-{name}',
            email=f'{hr_head.id}@organization.example.com',
            contact_number='+60123456789',
            address='Example address',
            status=Organization.Status.ACTIVE,
            created_by=hr_head,
        )

    def create_membership(self, user, organization, role):
        return OrganizationMembership.objects.create(organization=organization, user=user, role=role)

    def create_job(self, recruiter, organization=None, **overrides):
        return JobPosting.objects.create(
            organization=organization or self.organization,
            recruiter=recruiter,
            title=overrides.pop('title', 'Backend Engineer'),
            description='Build APIs',
            employment_type='Full-time',
            approximate_salary='5000.00',
            location='Kuala Lumpur',
            status=overrides.pop('status', JobPosting.Status.OPEN),
            **overrides,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user)

    @patch('apps.applications.views.schedule_resume_screening')
    def test_applicant_applies_once_to_open_job_without_running_screening(self, screening_placeholder):
        self.authenticate(self.applicant)

        response = self.client.post(reverse('job-apply', args=[self.job.id]))
        duplicate_response = self.client.post(reverse('job-apply', args=[self.job.id]))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], JobApplication.Status.SUBMITTED)
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        application = JobApplication.objects.get(job=self.job, applicant=self.applicant)
        screening_placeholder.assert_called_once_with(application)
        self.assertEqual(application.stage_history.count(), 0)

    def test_applicant_cannot_apply_to_non_open_job(self):
        draft_job = self.create_job(self.recruiter, status=JobPosting.Status.DRAFT)
        self.authenticate(self.applicant)

        response = self.client.post(reverse('job-apply', args=[draft_job.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(JobApplication.objects.filter(job=draft_job, applicant=self.applicant).exists())

    def test_withdrawal_changes_status_and_records_history_only_when_allowed(self):
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.applicant)

        response = self.client.delete(reverse('job-apply', args=[self.job.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, JobApplication.Status.WITHDRAWN)
        history = ApplicationStageHistory.objects.get(application=application)
        self.assertEqual(history.from_stage, JobApplication.Status.SUBMITTED)
        self.assertEqual(history.to_stage, JobApplication.Status.WITHDRAWN)
        self.assertEqual(history.changed_by, self.applicant)

        repeated_response = self.client.delete(reverse('job-apply', args=[self.job.id]))
        self.assertEqual(repeated_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(application.stage_history.count(), 1)

    def test_applicant_can_view_only_own_applications_and_history(self):
        own_application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        other_application = JobApplication.objects.create(job=self.job, applicant=self.other_applicant)
        own_application.change_status(JobApplication.Status.SCREENED, changed_by=self.recruiter)
        self.authenticate(self.applicant)

        list_response = self.client.get(reverse('application-list'))
        detail_response = self.client.get(reverse('application-detail', args=[own_application.id]))
        history_response = self.client.get(reverse('application-status-history', args=[own_application.id]))
        forbidden_detail_response = self.client.get(reverse('application-detail', args=[other_application.id]))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in list_response.data], [own_application.id])
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        self.assertEqual(history_response.data[0]['to_stage'], JobApplication.Status.SCREENED)
        self.assertEqual(forbidden_detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recruiter_views_only_applications_for_jobs_they_created(self):
        own_application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        colleague_job = self.create_job(self.other_recruiter, title='Designer')
        JobApplication.objects.create(job=colleague_job, applicant=self.other_applicant)
        self.authenticate(self.recruiter)

        response = self.client.get(reverse('application-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [own_application.id])

    def test_hr_head_views_applications_only_within_organization(self):
        own_application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        other_head = self.create_user('other-head@example.com', User.Role.HR_HEAD)
        external_recruiter = self.create_user('external-recruiter@example.com', User.Role.RECRUITER)
        other_organization = self.create_organization('Other Organization', other_head)
        self.create_membership(other_head, other_organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(external_recruiter, other_organization, OrganizationMembership.Role.RECRUITER)
        external_job = self.create_job(external_recruiter, organization=other_organization)
        JobApplication.objects.create(job=external_job, applicant=self.other_applicant)
        self.authenticate(self.hr_head)

        response = self.client.get(reverse('application-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [own_application.id])


class JobApplicationModelTests(TestCase):
    def setUp(self):
        self.hr_head = self.create_user('model-head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('model-recruiter@example.com', User.Role.RECRUITER)
        self.applicant = self.create_user('model-applicant@example.com', User.Role.APPLICANT)
        self.organization = Organization.objects.create(
            name='Model Test Organization',
            registration_no='REG-MODEL',
            email='model-organization@example.com',
            contact_number='+60123456789',
            address='Example address',
            status=Organization.Status.ACTIVE,
            created_by=self.hr_head,
        )
        self.job = JobPosting.objects.create(
            organization=self.organization,
            recruiter=self.recruiter,
            title='Backend Engineer',
            description='Build recruitment APIs with Django.',
            employment_type='full_time',
            approximate_salary='7000.00',
            location='Kuala Lumpur',
            status=JobPosting.Status.OPEN,
        )
        self.application = JobApplication.objects.create(job=self.job, applicant=self.applicant)

    def create_user(self, email, role):
        return User.objects.create_user(email=email, password='StrongPass123!', full_name=email, role=role)

    def test_change_status_updates_application_and_creates_stage_history(self):
        history = self.application.change_status(
            JobApplication.Status.SHORTLISTED,
            changed_by=self.recruiter,
            note='Strong candidate.',
        )

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.SHORTLISTED)
        self.assertEqual(ApplicationStageHistory.objects.count(), 1)
        self.assertEqual(history.from_stage, JobApplication.Status.SUBMITTED)
        self.assertEqual(history.to_stage, JobApplication.Status.SHORTLISTED)
        self.assertEqual(history.changed_by, self.recruiter)
        self.assertEqual(history.note, 'Strong candidate.')

    def test_change_status_does_not_create_history_when_status_is_unchanged(self):
        history = self.application.change_status(JobApplication.Status.SUBMITTED)

        self.assertIsNone(history)
        self.assertFalse(ApplicationStageHistory.objects.exists())

    def test_change_status_rejects_invalid_status(self):
        with self.assertRaises(ValidationError):
            self.application.change_status('invalid_status')

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.SUBMITTED)
        self.assertFalse(ApplicationStageHistory.objects.exists())

    def test_applicant_cannot_apply_for_the_same_job_twice(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            JobApplication.objects.create(job=self.job, applicant=self.applicant)
