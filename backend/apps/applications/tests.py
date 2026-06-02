from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.jobs.models import JobPosting
from apps.organizations.models import Organization
from apps.users.models import User

from .models import ApplicationStageHistory, JobApplication


class JobApplicationModelTests(TestCase):
    def setUp(self):
        self.hr_head = self.create_user('head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('recruiter@example.com', User.Role.RECRUITER)
        self.applicant = self.create_user('applicant@example.com', User.Role.APPLICANT)
        self.organization = Organization.objects.create(
            name='Example Organization',
            registration_no='REG-001',
            email='organization@example.com',
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
