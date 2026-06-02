from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import InterviewEvaluationForm, JobPosting, SavedJobPosting


class JobPostingAPITests(APITestCase):
    def setUp(self):
        self.hr_head = self.create_user('head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('recruiter@example.com', User.Role.RECRUITER)
        self.applicant = self.create_user('applicant@example.com', User.Role.APPLICANT)
        self.organization = self.create_organization('Example Organization', self.hr_head)
        self.create_membership(self.hr_head, self.organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.job_payload = {
            'title': 'Backend Engineer',
            'description': 'Build recruitment APIs with Django.',
            'employment_type': 'full_time',
            'approximate_salary': '7000.00',
            'location': 'Kuala Lumpur',
            'status': JobPosting.Status.OPEN,
        }

    def create_user(self, email, role):
        return User.objects.create_user(email=email, password='StrongPass123!', full_name=email, role=role)

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

    def create_job(self, **overrides):
        data = {**self.job_payload, **overrides}
        return JobPosting.objects.create(organization=self.organization, recruiter=self.recruiter, **data)

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def test_recruiter_can_create_patch_and_delete_job_for_own_organization(self):
        self.authenticate(self.recruiter)

        create_response = self.client.post(reverse('job-list-create'), self.job_payload, format='json')
        job_id = create_response.data['id']
        patch_response = self.client.patch(reverse('job-detail', args=[job_id]), {'location': 'Remote'}, format='json')
        delete_response = self.client.delete(reverse('job-detail', args=[job_id]))

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data['organization'], self.organization.id)
        self.assertEqual(create_response.data['recruiter'], self.recruiter.id)
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data['location'], 'Remote')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(JobPosting.objects.filter(id=job_id).exists())

    def test_recruiter_cannot_manage_another_organizations_job(self):
        other_head = self.create_user('other-head@example.com', User.Role.HR_HEAD)
        other_recruiter = self.create_user('other-recruiter@example.com', User.Role.RECRUITER)
        other_organization = self.create_organization('Other Organization', other_head)
        self.create_membership(other_head, other_organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(other_recruiter, other_organization, OrganizationMembership.Role.RECRUITER)
        other_job = JobPosting.objects.create(
            organization=other_organization,
            recruiter=other_recruiter,
            **self.job_payload,
        )
        self.authenticate(self.recruiter)

        response = self.client.patch(reverse('job-detail', args=[other_job.id]), {'location': 'Remote'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        other_job.refresh_from_db()
        self.assertEqual(other_job.location, 'Kuala Lumpur')

    def test_hr_head_lists_organization_jobs_but_cannot_create_jobs(self):
        job = self.create_job()
        self.authenticate(self.hr_head)

        list_response = self.client.get(reverse('job-list-create'))
        create_response = self.client.post(reverse('job-list-create'), self.job_payload, format='json')

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in list_response.data], [job.id])
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_applicant_only_sees_open_jobs_and_can_search_and_filter(self):
        matching_job = self.create_job()
        self.create_job(title='Designer', location='Penang')
        self.create_job(title='Backend Engineer Intern', status=JobPosting.Status.DRAFT)
        self.authenticate(self.applicant)

        response = self.client.get(
            reverse('job-list-create'),
            {'search': 'Django', 'title': 'Backend', 'location': 'Kuala', 'employment_type': 'full'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [matching_job.id])

    def test_recruiter_can_configure_requirements_only_when_weights_sum_to_one(self):
        job = self.create_job()
        self.authenticate(self.recruiter)
        requirements_url = reverse('job-requirements', args=[job.id])
        invalid_payload = {
            'requirements': [
                {'requirement_type': 'skill', 'description': 'Python', 'weight_score': '0.60', 'minimum_threshold': '0.50'},
                {'requirement_type': 'experience', 'description': 'Three years', 'weight_score': '0.30', 'minimum_threshold': '0.50'},
            ]
        }

        invalid_response = self.client.post(requirements_url, invalid_payload, format='json')
        normalized_response = self.client.post(
            requirements_url,
            {**invalid_payload, 'normalize_weights': True},
            format='json',
        )

        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(normalized_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(job.requirements.count(), 2)
        self.assertEqual(sum(job.requirements.values_list('weight_score', flat=True)), Decimal('1.00'))

    def test_recruiter_can_create_evaluation_form_and_duplicate_complete_job_configuration(self):
        job = self.create_job()
        self.authenticate(self.recruiter)
        self.client.post(
            reverse('job-requirements', args=[job.id]),
            {
                'requirements': [
                    {'requirement_type': 'skill', 'description': 'Python', 'weight_score': '1.00', 'minimum_threshold': '0.50'},
                ]
            },
            format='json',
        )
        form_response = self.client.post(
            reverse('job-evaluation-form', args=[job.id]),
            {
                'title': 'Technical Interview',
                'criteria': [
                    {'criterion_name': 'API design', 'description': 'Design quality', 'max_score': '10.00', 'weight_score': '1.00'},
                ],
            },
            format='json',
        )

        duplicate_response = self.client.post(reverse('job-duplicate', args=[job.id]))

        self.assertEqual(form_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate_response.status_code, status.HTTP_201_CREATED)
        duplicate = JobPosting.objects.get(id=duplicate_response.data['id'])
        self.assertEqual(duplicate.status, JobPosting.Status.DRAFT)
        self.assertEqual(duplicate.requirements.count(), 1)
        self.assertTrue(InterviewEvaluationForm.objects.filter(job=duplicate).exists())
        self.assertEqual(duplicate.interview_evaluation_form.criteria.count(), 1)

    def test_applicant_can_save_list_and_unsave_open_job(self):
        job = self.create_job()
        self.authenticate(self.applicant)
        save_url = reverse('job-save', args=[job.id])

        save_response = self.client.post(save_url)
        repeated_save_response = self.client.post(save_url)
        list_response = self.client.get(reverse('saved-job-list'))
        unsave_response = self.client.delete(save_url)

        self.assertEqual(save_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(repeated_save_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in list_response.data], [job.id])
        self.assertTrue(list_response.data[0]['is_saved'])
        self.assertEqual(unsave_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SavedJobPosting.objects.filter(applicant=self.applicant, job=job).exists())

    def test_applicant_cannot_view_or_save_draft_job(self):
        job = self.create_job(status=JobPosting.Status.DRAFT)
        self.authenticate(self.applicant)

        detail_response = self.client.get(reverse('job-detail', args=[job.id]))
        save_response = self.client.post(reverse('job-save', args=[job.id]))

        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(save_response.status_code, status.HTTP_404_NOT_FOUND)
