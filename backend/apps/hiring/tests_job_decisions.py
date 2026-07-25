from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import JobApplication
from apps.evaluations.models import InterviewEvaluation
from apps.hiring.models import JobHiringDecision
from apps.interviews.models import Interview
from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


class JobLevelHiringDecisionFlowTests(APITestCase):
    def setUp(self):
        self.hr = User.objects.create_user(email='hr-flow@example.com', password='pass', full_name='Hiring Manager', role=User.Role.HR_HEAD)
        self.recruiter = User.objects.create_user(email='recruiter-flow@example.com', password='pass', full_name='Recruiter', role=User.Role.RECRUITER)
        self.applicant = User.objects.create_user(email='applicant-flow@example.com', password='pass', full_name='Applicant', role=User.Role.APPLICANT)
        self.interviewer = User.objects.create_user(email='interviewer-flow@example.com', password='pass', full_name='Interviewer', role=User.Role.INTERVIEWER)
        self.organization = Organization.objects.create(name='Flow Org', registration_no='FLOW-1', email='flow@example.com', contact_number='1', address='Address', created_by=self.hr)
        for user, role in ((self.hr, OrganizationMembership.Role.HR_HEAD), (self.recruiter, OrganizationMembership.Role.RECRUITER), (self.interviewer, OrganizationMembership.Role.INTERVIEWER)):
            OrganizationMembership.objects.create(organization=self.organization, user=user, role=role)
        self.job = JobPosting.objects.create(organization=self.organization, recruiter=self.recruiter, title='Engineer', description='Build', employment_type='Full time', location='Remote', status=JobPosting.Status.OPEN, vacancies=1)
        self.application = JobApplication.objects.create(job=self.job, applicant=self.applicant, status=JobApplication.Status.UNDER_REVIEW, final_score='88.00')

    def close_intake(self):
        self.client.force_authenticate(self.recruiter)
        return self.client.post(reverse('job-close-intake', args=[self.job.id]))

    def submit(self, decision_type='recommend_hire', application_ids=None):
        self.client.force_authenticate(self.recruiter)
        return self.client.post(reverse('job-hiring-decision-list-create'), {
            'job_posting': self.job.id,
            'decision_type': decision_type,
            'application_ids': [self.application.id] if application_ids is None else application_ids,
            'justification': 'Evidence supports this job-level decision.',
        }, format='json')

    def test_close_intake_blocks_new_applications_and_marks_ready(self):
        response = self.close_intake()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['readiness']['ready'])
        self.assertEqual(response.data['job']['status'], JobPosting.Status.CLOSED)
        self.client.force_authenticate(self.applicant)
        apply_response = self.client.post(reverse('job-apply', args=[self.job.id]), {}, format='json')
        self.assertEqual(apply_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_open_job_and_vacancy_limit_are_enforced(self):
        self.assertEqual(self.submit().status_code, status.HTTP_400_BAD_REQUEST)
        self.close_intake()
        second = User.objects.create_user(email='second-flow@example.com', password='pass', full_name='Second', role=User.Role.APPLICANT)
        second_application = JobApplication.objects.create(job=self.job, applicant=second, status=JobApplication.Status.UNDER_REVIEW)
        response = self.submit(application_ids=[self.application.id, second_application.id])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('application_ids', response.data)

    def test_comparison_and_recommend_hire_are_job_scoped(self):
        self.close_intake()
        self.client.force_authenticate(self.recruiter)
        comparison = self.client.get(reverse('job-applicant-comparison', args=[self.job.id]))
        self.assertEqual(comparison.status_code, status.HTTP_200_OK)
        self.assertEqual(comparison.data['applicants'][0]['applicant_name'], 'Applicant')
        response = self.submit()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['items'][0]['application']['id'], self.application.id)

    def test_pending_decision_returns_its_specific_error_instead_of_readiness_error(self):
        self.close_intake()
        self.assertEqual(self.submit().status_code, status.HTTP_201_CREATED)

        duplicate = self.submit()

        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already has a decision pending', str(duplicate.data))

    def test_comparison_requires_all_panel_scorecards_before_application_is_eligible(self):
        panel_interviewer = User.objects.create_user(
            email='comparison-panel@example.com', password='pass', full_name='Panel', role=User.Role.INTERVIEWER,
        )
        OrganizationMembership.objects.create(
            organization=self.organization, user=panel_interviewer, role=OrganizationMembership.Role.INTERVIEWER,
        )
        interview = Interview.objects.create(
            application=self.application, organization=self.organization, recruiter=self.recruiter,
            interviewer=self.interviewer, status=Interview.Status.EVALUATION_SUBMITTED,
        )
        interview.panel_interviewers.add(panel_interviewer)
        InterviewEvaluation.objects.create(
            interview=interview, interviewer=self.interviewer, total_score='8.00', overall_comment='Submitted.',
        )
        self.close_intake()
        self.client.force_authenticate(self.recruiter)

        comparison = self.client.get(reverse('job-applicant-comparison', args=[self.job.id]))

        self.assertEqual(comparison.status_code, status.HTTP_200_OK)
        applicant = comparison.data['applicants'][0]
        self.assertEqual(applicant['evaluation_status'], 'pending')
        self.assertEqual(applicant['scorecards_submitted'], 1)
        self.assertEqual(applicant['scorecards_required'], 2)
        self.assertFalse(applicant['eligible_for_decision'])

    def test_no_hire_requires_no_applicants_and_hr_can_approve(self):
        self.close_intake()
        response = self.submit('recommend_no_hire', [])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.hr)
        review = self.client.post(reverse('job-hiring-decision-approve', args=[response.data['id']]), {'hr_remarks': 'No suitable applicant.'}, format='json')
        self.assertEqual(review.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobPosting.Status.CLOSED)

    def test_hr_rejects_whole_decision_and_applicant_cannot_access_it(self):
        self.close_intake()
        response = self.submit()
        self.client.force_authenticate(self.hr)
        review = self.client.post(reverse('job-hiring-decision-reject', args=[response.data['id']]), {'hr_remarks': 'Revise selection.'}, format='json')
        self.assertEqual(review.status_code, status.HTTP_200_OK)
        self.assertEqual(review.data['status'], JobHiringDecision.Status.REJECTED)
        self.client.force_authenticate(self.applicant)
        self.assertEqual(self.client.get(reverse('job-hiring-decision-list-create')).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse('job-applicant-comparison', args=[self.job.id])).status_code, status.HTTP_403_FORBIDDEN)

    def test_interviewer_cannot_submit_or_review(self):
        self.close_intake()
        self.client.force_authenticate(self.interviewer)
        self.assertEqual(self.client.post(reverse('job-hiring-decision-list-create'), {'job_posting': self.job.id}).status_code, status.HTTP_403_FORBIDDEN)
        decision = self.submit().data
        self.client.force_authenticate(self.interviewer)
        self.assertEqual(self.client.post(reverse('job-hiring-decision-approve', args=[decision['id']])).status_code, status.HTTP_403_FORBIDDEN)

    def test_decision_waits_for_scorecards_from_every_panel_interviewer(self):
        panel_interviewer = User.objects.create_user(
            email='panel-interviewer-flow@example.com', password='pass',
            full_name='Panel Interviewer', role=User.Role.INTERVIEWER,
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=panel_interviewer,
            role=OrganizationMembership.Role.INTERVIEWER,
        )
        interview = Interview.objects.create(
            application=self.application,
            organization=self.organization,
            recruiter=self.recruiter,
            interviewer=self.interviewer,
            status=Interview.Status.EVALUATION_SUBMITTED,
        )
        interview.panel_interviewers.add(panel_interviewer)

        self.close_intake()
        blocked_response = self.submit()
        self.assertEqual(blocked_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scorecards from all assigned interviewers', str(blocked_response.data))

        InterviewEvaluation.objects.create(
            interview=interview,
            interviewer=self.interviewer,
            total_score='8.00',
            overall_comment='Primary interviewer scorecard.',
        )
        blocked_response = self.submit()
        self.assertEqual(blocked_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scorecards from all assigned interviewers', str(blocked_response.data))

        InterviewEvaluation.objects.create(
            interview=interview,
            interviewer=panel_interviewer,
            total_score='8.50',
            overall_comment='Panel interviewer scorecard.',
        )
        allowed_response = self.submit()
        self.assertEqual(allowed_response.status_code, status.HTTP_201_CREATED, allowed_response.data)
