from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.applications.models import JobApplication
from apps.billing.models import Payment, Subscription
from apps.evaluations.models import InterviewAISummary
from apps.hiring.models import JobOffer
from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import ApplicantResume, User


@override_settings(MEDIA_ROOT='/tmp/hrrecruit-seed-demo-test-media')
class SeedDemoDataCommandTests(TestCase):
    def run_seed_command(self):
        call_command('seed_demo_data', verbosity=0)

    def test_seed_command_creates_core_demo_records(self):
        self.run_seed_command()

        self.assertTrue(User.objects.filter(email='demo.hrhead@example.com', role=User.Role.HR_HEAD).exists())
        self.assertTrue(User.objects.filter(email='demo.recruiter@example.com', role=User.Role.RECRUITER).exists())
        self.assertTrue(User.objects.filter(email='demo.interviewer@example.com', role=User.Role.INTERVIEWER).exists())
        self.assertTrue(User.objects.filter(email='demo.applicant@example.com', role=User.Role.APPLICANT).exists())
        self.assertTrue(Organization.objects.filter(registration_no='DEMO-TN-001').exists())
        self.assertTrue(JobPosting.objects.filter(title='Software Engineer').exists())
        self.assertTrue(JobPosting.objects.filter(title='Data Analyst').exists())
        application = JobApplication.objects.get(
            job__title='Software Engineer',
            applicant__email='demo.applicant@example.com',
        )
        self.assertIsNotNone(application.resume_id)
        self.assertEqual(application.resume.title, 'Software Engineer Resume')
        self.assertEqual(ApplicantResume.objects.filter(applicant__email='demo.applicant@example.com').count(), 2)
        self.assertTrue(Subscription.objects.filter(organization__registration_no='DEMO-TN-001').exists())
        self.assertTrue(JobOffer.objects.filter(application=application, salary_amount='6500.00').exists())
        self.assertTrue(InterviewAISummary.objects.filter(summary_json__transparency__provider='mock').exists())
        self.assertTrue(Payment.objects.filter(transaction_reference='DEMO-SEED-PAYMENT', due_at__isnull=False).exists())

    def test_seed_command_is_idempotent_for_core_records(self):
        self.run_seed_command()
        counts_after_first_run = {
            'users': User.objects.filter(email__startswith='demo.').count(),
            'organizations': Organization.objects.filter(registration_no='DEMO-TN-001').count(),
            'memberships': OrganizationMembership.objects.filter(organization__registration_no='DEMO-TN-001').count(),
            'jobs': JobPosting.objects.filter(organization__registration_no='DEMO-TN-001').count(),
            'applications': JobApplication.objects.filter(applicant__email='demo.applicant@example.com').count(),
            'resumes': ApplicantResume.objects.filter(applicant__email='demo.applicant@example.com').count(),
        }

        self.run_seed_command()

        self.assertEqual(User.objects.filter(email__startswith='demo.').count(), counts_after_first_run['users'])
        self.assertEqual(Organization.objects.filter(registration_no='DEMO-TN-001').count(), counts_after_first_run['organizations'])
        self.assertEqual(OrganizationMembership.objects.filter(organization__registration_no='DEMO-TN-001').count(), counts_after_first_run['memberships'])
        self.assertEqual(JobPosting.objects.filter(organization__registration_no='DEMO-TN-001').count(), counts_after_first_run['jobs'])
        self.assertEqual(JobApplication.objects.filter(applicant__email='demo.applicant@example.com').count(), counts_after_first_run['applications'])
        self.assertEqual(ApplicantResume.objects.filter(applicant__email='demo.applicant@example.com').count(), counts_after_first_run['resumes'])
