from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import JobApplication
from apps.hiring.models import JobHiringRecommendation
from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


class JobLevelHiringRecommendationFlowTests(APITestCase):
    def setUp(self):
        self.hr = User.objects.create_user(email='hr-flow@example.com', password='pass', full_name='HR Head', role=User.Role.HR_HEAD)
        self.recruiter = User.objects.create_user(email='recruiter-flow@example.com', password='pass', full_name='Recruiter', role=User.Role.RECRUITER)
        self.applicant = User.objects.create_user(email='applicant-flow@example.com', password='pass', full_name='Applicant', role=User.Role.APPLICANT)
        self.interviewer = User.objects.create_user(email='interviewer-flow@example.com', password='pass', full_name='Interviewer', role=User.Role.INTERVIEWER)
        self.organization = Organization.objects.create(name='Flow Org', registration_no='FLOW-1', email='flow@example.com', contact_number='1', address='Address', created_by=self.hr)
        for user, role in ((self.hr, OrganizationMembership.Role.HR_HEAD), (self.recruiter, OrganizationMembership.Role.RECRUITER), (self.interviewer, OrganizationMembership.Role.INTERVIEWER)):
            OrganizationMembership.objects.create(organization=self.organization, user=user, role=role)
        self.job = JobPosting.objects.create(organization=self.organization, recruiter=self.recruiter, title='Engineer', description='Build', employment_type='Full time', location='Remote', status=JobPosting.Status.OPEN, vacancies=1)
        self.application = JobApplication.objects.create(job=self.job, applicant=self.applicant, status=JobApplication.Status.EVALUATION_SUBMITTED, final_score='88.00')

    def close_intake(self):
        self.client.force_authenticate(self.recruiter)
        return self.client.post(reverse('job-close-intake', args=[self.job.id]))

    def submit(self, recommendation_type='recommend_hire', application_ids=None):
        self.client.force_authenticate(self.recruiter)
        return self.client.post(reverse('job-hiring-recommendation-list-create'), {
            'job_posting': self.job.id,
            'recommendation_type': recommendation_type,
            'application_ids': [self.application.id] if application_ids is None else application_ids,
            'justification': 'Evidence supports this job-level recommendation.',
        }, format='json')

    def test_close_intake_blocks_new_applications_and_marks_ready(self):
        response = self.close_intake()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['readiness']['ready'])
        self.assertEqual(response.data['job']['status'], JobPosting.Status.READY_FOR_RECOMMENDATION)
        self.client.force_authenticate(self.applicant)
        apply_response = self.client.post(reverse('job-apply', args=[self.job.id]), {}, format='json')
        self.assertEqual(apply_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_open_job_and_vacancy_limit_are_enforced(self):
        self.assertEqual(self.submit().status_code, status.HTTP_400_BAD_REQUEST)
        self.close_intake()
        second = User.objects.create_user(email='second-flow@example.com', password='pass', full_name='Second', role=User.Role.APPLICANT)
        second_application = JobApplication.objects.create(job=self.job, applicant=second, status=JobApplication.Status.EVALUATION_SUBMITTED)
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

    def test_no_hire_requires_no_applicants_and_hr_can_approve(self):
        self.close_intake()
        response = self.submit('recommend_no_hire', [])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.hr)
        review = self.client.post(reverse('job-hiring-recommendation-approve', args=[response.data['id']]), {'hr_remarks': 'No suitable applicant.'}, format='json')
        self.assertEqual(review.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobPosting.Status.CLOSED_NO_HIRE)

    def test_hr_rejects_whole_recommendation_and_applicant_cannot_access_it(self):
        self.close_intake()
        response = self.submit()
        self.client.force_authenticate(self.hr)
        review = self.client.post(reverse('job-hiring-recommendation-reject', args=[response.data['id']]), {'hr_remarks': 'Revise selection.'}, format='json')
        self.assertEqual(review.status_code, status.HTTP_200_OK)
        self.assertEqual(review.data['status'], JobHiringRecommendation.Status.REJECTED)
        self.client.force_authenticate(self.applicant)
        self.assertEqual(self.client.get(reverse('job-hiring-recommendation-list-create')).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse('job-applicant-comparison', args=[self.job.id])).status_code, status.HTTP_403_FORBIDDEN)

    def test_interviewer_cannot_submit_or_review(self):
        self.close_intake()
        self.client.force_authenticate(self.interviewer)
        self.assertEqual(self.client.post(reverse('job-hiring-recommendation-list-create'), {'job_posting': self.job.id}).status_code, status.HTTP_403_FORBIDDEN)
        recommendation = self.submit().data
        self.client.force_authenticate(self.interviewer)
        self.assertEqual(self.client.post(reverse('job-hiring-recommendation-approve', args=[recommendation['id']])).status_code, status.HTTP_403_FORBIDDEN)
