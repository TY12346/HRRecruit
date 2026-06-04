from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.evaluations.models import InterviewEvaluation
from apps.hiring.models import JobOffer
from apps.interviews.models import Interview
from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


class AnalyticsAPITests(APITestCase):
    def setUp(self):
        self.hr_head = self.create_user('head@example.com', User.Role.HR_HEAD, 'HR Head')
        self.recruiter = self.create_user('recruiter@example.com', User.Role.RECRUITER, 'Recruiter One')
        self.interviewer = self.create_user('interviewer@example.com', User.Role.INTERVIEWER, 'Interviewer One')
        self.applicant = self.create_user('applicant@example.com', User.Role.APPLICANT, 'Applicant One')
        self.applicant_two = self.create_user('applicant2@example.com', User.Role.APPLICANT, 'Applicant Two')
        self.applicant_three = self.create_user('applicant3@example.com', User.Role.APPLICANT, 'Applicant Three')
        self.other_hr_head = self.create_user('other-head@example.com', User.Role.HR_HEAD, 'Other HR Head')
        self.other_recruiter = self.create_user('other-recruiter@example.com', User.Role.RECRUITER, 'Other Recruiter')
        self.other_applicant = self.create_user('other-applicant@example.com', User.Role.APPLICANT, 'Other Applicant')

        self.organization = self.create_organization('Example Organization', self.hr_head, 'REG-ANA')
        self.other_organization = self.create_organization('Other Organization', self.other_hr_head, 'REG-ANA-OTHER')
        self.create_membership(self.hr_head, self.organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.create_membership(self.interviewer, self.organization, OrganizationMembership.Role.INTERVIEWER)
        self.create_membership(self.other_hr_head, self.other_organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.other_recruiter, self.other_organization, OrganizationMembership.Role.RECRUITER)

        self.job = self.create_job(self.recruiter, self.organization, 'Backend Engineer')
        self.other_job = self.create_job(self.other_recruiter, self.other_organization, 'External Job')
        self.submitted_application = self.create_application(self.job, self.applicant, JobApplication.Status.SUBMITTED)
        self.shortlisted_application = self.create_application(self.job, self.applicant_two, JobApplication.Status.SHORTLISTED)
        self.hired_application = self.create_application(self.job, self.applicant_three, JobApplication.Status.HIRED)
        self.other_application = self.create_application(self.other_job, self.other_applicant, JobApplication.Status.HIRED)

        applied_at = timezone.now() - timezone.timedelta(days=10)
        hired_at = timezone.now() - timezone.timedelta(days=1)
        JobApplication.objects.filter(id=self.hired_application.id).update(applied_at=applied_at, updated_at=hired_at)
        ApplicationStageHistory.objects.create(
            application=self.hired_application,
            from_stage=JobApplication.Status.OFFER_ACCEPTED,
            to_stage=JobApplication.Status.HIRED,
            changed_by=self.recruiter,
            note='Candidate accepted and joined.',
        )
        ApplicationStageHistory.objects.filter(application=self.hired_application).update(changed_at=hired_at)

        self.interview = Interview.objects.create(
            application=self.shortlisted_application,
            organization=self.organization,
            recruiter=self.recruiter,
            interviewer=self.interviewer,
            status=Interview.Status.COMPLETED,
        )
        InterviewEvaluation.objects.create(
            interview=self.interview,
            interviewer=self.interviewer,
            total_score='88.50',
            overall_comment='Strong candidate.',
        )
        JobOffer.objects.create(
            application=self.hired_application,
            offer_message='Welcome aboard.',
            offer_status=JobOffer.OfferStatus.ACCEPTED,
            respond_deadline=timezone.now() + timezone.timedelta(days=7),
        )

    def create_user(self, email, role, full_name):
        return User.objects.create_user(email=email, password='test-pass-123', full_name=full_name, role=role)

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

    def create_job(self, recruiter, organization, title):
        return JobPosting.objects.create(
            organization=organization,
            recruiter=recruiter,
            title=title,
            description='Build APIs',
            employment_type='Full-time',
            approximate_salary='5000.00',
            location='Kuala Lumpur',
            status=JobPosting.Status.OPEN,
        )

    def create_application(self, job, applicant, application_status):
        return JobApplication.objects.create(job=job, applicant=applicant, status=application_status)

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def test_recruiter_dashboard_returns_own_organization_job_metrics_only(self):
        self.authenticate(self.recruiter)

        response = self.client.get(reverse('analytics-recruiter-dashboard'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dashboard'], 'recruiter')
        self.assertEqual(response.data['organization']['id'], self.organization.id)
        self.assertEqual(response.data['metrics']['total_job_postings'], 1)
        self.assertEqual(response.data['metrics']['total_applications'], 3)
        self.assertEqual(response.data['metrics']['hired_count'], 1)
        self.assertEqual(response.data['metrics']['recruiter_hire_count'], 1)
        self.assertEqual(response.data['metrics']['interviewer_evaluation_count'], 1)
        self.assertEqual(response.data['metrics']['offer_acceptance_rate'], 100.0)
        self.assertIn('candidate_funnel', response.data['charts'])
        self.assertNotEqual(response.data['metrics']['total_applications'], 4)

    def test_interviewer_dashboard_returns_assigned_interview_metrics(self):
        self.authenticate(self.interviewer)

        response = self.client.get(reverse('analytics-interviewer-dashboard'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dashboard'], 'interviewer')
        self.assertEqual(response.data['metrics']['assigned_interviews'], 1)
        self.assertEqual(response.data['metrics']['completed_interviews'], 1)
        self.assertEqual(response.data['metrics']['interviewer_evaluation_count'], 1)
        self.assertEqual(response.data['metrics']['average_evaluation_score'], 88.5)
        self.assertEqual(response.data['metrics']['total_applications'], 1)

    def test_hr_head_dashboard_and_overview_include_organization_performance_only(self):
        self.authenticate(self.hr_head)

        dashboard_response = self.client.get(reverse('analytics-hr-head-dashboard'))
        overview_response = self.client.get(reverse('analytics-organization-overview'))

        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertEqual(overview_response.status_code, status.HTTP_200_OK)
        self.assertEqual(dashboard_response.data['metrics']['total_job_postings'], 1)
        self.assertEqual(dashboard_response.data['metrics']['total_applications'], 3)
        self.assertEqual(dashboard_response.data['metrics']['hiring_success_rate'], 33.33)
        self.assertEqual(dashboard_response.data['recruiter_performance'][0]['hire_count'], 1)
        self.assertEqual(dashboard_response.data['interviewer_performance'][0]['evaluation_count'], 1)
        self.assertEqual(overview_response.data['dashboard'], 'organization_overview')

    def test_job_funnel_is_organization_isolated(self):
        self.authenticate(self.hr_head)

        own_response = self.client.get(reverse('analytics-job-funnel', args=[self.job.id]))
        external_response = self.client.get(reverse('analytics-job-funnel', args=[self.other_job.id]))

        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertEqual(own_response.data['job']['id'], self.job.id)
        self.assertEqual(own_response.data['metrics']['total_applications'], 3)
        self.assertEqual(external_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_applicant_cannot_access_analytics(self):
        self.authenticate(self.applicant)

        response = self.client.get(reverse('analytics-recruiter-dashboard'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
