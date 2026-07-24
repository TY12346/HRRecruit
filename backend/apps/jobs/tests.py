from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from django.utils import timezone

from apps.billing.models import Subscription, SubscriptionPlan
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import EvaluationCriterion, InterviewEvaluationForm, JobPosting, SavedJobPosting


class JobPostingAPITests(APITestCase):
    def setUp(self):
        self.hr_head = self.create_user('head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('recruiter@example.com', User.Role.RECRUITER)
        self.applicant = self.create_user('applicant@example.com', User.Role.APPLICANT)
        self.organization = self.create_organization('Example Organization', self.hr_head)
        self.create_membership(self.hr_head, self.organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.plan, _ = SubscriptionPlan.objects.get_or_create(
            name=SubscriptionPlan.Name.PRO,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            defaults={
                'max_job_postings': 10,
                'price': '149.00',
                'features_description': 'Test plan',
            },
        )
        Subscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
            status=Subscription.Status.ACTIVE,
        )
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

    def test_recruiter_cannot_create_job_directly_but_can_patch_and_delete_own_job(self):
        job = self.create_job(status=JobPosting.Status.DRAFT)
        self.authenticate(self.recruiter)

        create_response = self.client.post(reverse('job-list-create'), self.job_payload, format='json')
        patch_response = self.client.patch(reverse('job-detail', args=[job.id]), {'location': 'Remote'}, format='json')
        delete_response = self.client.delete(reverse('job-detail', args=[job.id]))

        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data['location'], 'Remote')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(JobPosting.objects.filter(id=job.id).exists())

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

    def test_recruiter_cannot_view_a_colleagues_job_in_the_same_organization(self):
        colleague = self.create_user('colleague@example.com', User.Role.RECRUITER)
        self.create_membership(colleague, self.organization, OrganizationMembership.Role.RECRUITER)
        own_job = self.create_job(title='Own job')
        colleague_job = JobPosting.objects.create(
            organization=self.organization,
            recruiter=colleague,
            **self.job_payload,
        )
        self.authenticate(self.recruiter)

        list_response = self.client.get(reverse('job-list-create'))
        detail_response = self.client.get(reverse('job-detail', args=[colleague_job.id]))
        update_response = self.client.patch(reverse('job-detail', args=[colleague_job.id]), {'location': 'Remote'}, format='json')

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in list_response.data], [own_job.id])
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)

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
        job = self.create_job(status=JobPosting.Status.DRAFT)
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

    def test_recruiter_can_create_evaluation_scorecard_but_cannot_duplicate_job_configuration(self):
        job = self.create_job(status=JobPosting.Status.DRAFT)
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
            reverse('job-evaluation-scorecard', args=[job.id]),
            {
                'title': 'Technical Interview Scorecard',
                'criteria': [
                    {'criterion_name': 'API design', 'description': 'Design quality', 'max_score': '10.00', 'weight_score': '1.00'},
                ],
            },
            format='json',
        )

        duplicate_response = self.client.post(reverse('job-duplicate', args=[job.id]))

        self.assertEqual(form_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(InterviewEvaluationForm.objects.filter(job=job).exists())
        self.assertEqual(job.interview_evaluation_form.criteria.count(), 1)


    def test_hr_approval_creates_draft_job_for_recruiter_configuration(self):
        self.authenticate(self.recruiter)
        requisition_payload = {
            'title': 'Product Designer',
            'description': 'Design applicant experiences.',
            'employment_type': 'full_time',
            'salary_range': 'RM 6,000 - RM 8,000',
            'location': 'Kuala Lumpur',
            'core_responsibilities': 'Create flows and prototypes.',
            'requirements_qualifications': 'Portfolio and product design experience.',
            'department': 'Product',
            'target_start_date': str(timezone.localdate() + timedelta(days=30)),
            'benefits_perks': 'Allowance and bonus.',
            'position_status': 'new_headcount',
            'reason_for_hire': 'New product roadmap.',
            'impact_of_not_hiring': 'Delayed releases.',
        }
        create_response = self.client.post(reverse('job-requisition-list-create'), requisition_payload, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        self.authenticate(self.hr_head)
        approve_response = self.client.post(reverse('job-requisition-approve', args=[create_response.data['id']]))

        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        job = JobPosting.objects.get(id=approve_response.data['job_posting_id'])
        self.assertEqual(job.status, JobPosting.Status.DRAFT)
        self.assertEqual(job.salary_range, requisition_payload['salary_range'])
        self.assertEqual(job.core_responsibilities, requisition_payload['core_responsibilities'])

    def test_recruiter_cannot_open_approved_job_before_requirements_and_scorecard(self):
        job = self.create_job(status=JobPosting.Status.DRAFT)
        self.authenticate(self.recruiter)

        no_config_response = self.client.patch(reverse('job-detail', args=[job.id]), {'status': JobPosting.Status.OPEN}, format='json')
        self.client.post(
            reverse('job-requirements', args=[job.id]),
            {
                'requirements': [
                    {'requirement_type': 'skill', 'description': 'Python', 'weight_score': '1.00', 'minimum_threshold': '0.50'},
                ]
            },
            format='json',
        )
        no_scorecard_response = self.client.patch(reverse('job-detail', args=[job.id]), {'status': JobPosting.Status.OPEN}, format='json')
        self.client.post(
            reverse('job-evaluation-scorecard', args=[job.id]),
            {
                'title': 'Interview Evaluation Scorecard',
                'criteria': [
                    {'criterion_name': 'Technical fit', 'description': 'Technical quality', 'max_score': '10.00', 'weight_score': '1.00'},
                ],
            },
            format='json',
        )
        open_response = self.client.patch(reverse('job-detail', args=[job.id]), {'status': JobPosting.Status.OPEN}, format='json')

        self.assertEqual(no_config_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(no_scorecard_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(open_response.status_code, status.HTTP_200_OK)
        self.assertEqual(open_response.data['status'], JobPosting.Status.OPEN)

    def test_recruiter_cannot_open_job_with_an_empty_scorecard(self):
        job = self.create_job(status=JobPosting.Status.DRAFT)
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
        form = InterviewEvaluationForm.objects.create(job=job, title='Empty scorecard')

        empty_scorecard_response = self.client.patch(
            reverse('job-detail', args=[job.id]), {'status': JobPosting.Status.OPEN}, format='json'
        )
        EvaluationCriterion.objects.create(
            form=form,
            criterion_name='Technical fit',
            description='Technical quality',
            max_score='10.00',
            weight_score='1.00',
        )
        open_response = self.client.patch(
            reverse('job-detail', args=[job.id]), {'status': JobPosting.Status.OPEN}, format='json'
        )

        self.assertEqual(empty_scorecard_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non-empty interview evaluation scorecard', empty_scorecard_response.data['status'][0])
        self.assertEqual(open_response.status_code, status.HTTP_200_OK)

    def test_scorecard_creation_rejects_empty_criteria(self):
        job = self.create_job(status=JobPosting.Status.DRAFT)
        self.authenticate(self.recruiter)

        response = self.client.post(
            reverse('job-evaluation-scorecard', args=[job.id]),
            {'title': 'Empty scorecard', 'criteria': []},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('criteria', response.data)

    def test_recruiter_cannot_change_requirements_after_job_is_posted(self):
        job = self.create_job(status=JobPosting.Status.DRAFT)
        self.authenticate(self.recruiter)
        requirements_url = reverse('job-requirements', args=[job.id])
        initial_requirements = {
            'requirements': [
                {'requirement_type': 'skill', 'description': 'Python', 'weight_score': '1.00', 'minimum_threshold': '0.50'},
            ]
        }
        self.client.post(requirements_url, initial_requirements, format='json')
        self.client.post(
            reverse('job-evaluation-scorecard', args=[job.id]),
            {
                'title': 'Interview Evaluation Scorecard',
                'criteria': [
                    {'criterion_name': 'Technical fit', 'description': 'Technical quality', 'max_score': '10.00', 'weight_score': '1.00'},
                ],
            },
            format='json',
        )
        self.client.patch(reverse('job-detail', args=[job.id]), {'status': JobPosting.Status.OPEN}, format='json')

        response = self.client.post(
            requirements_url,
            {
                'requirements': [
                    {'requirement_type': 'skill', 'description': 'Java', 'weight_score': '1.00', 'minimum_threshold': '0.50'},
                ]
            },
            format='json',
        )

        job.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be changed once this job has been posted', response.data['requirements'][0])
        self.assertIsNotNone(job.requirements_locked_at)
        self.assertEqual(list(job.requirements.values_list('description', flat=True)), ['Python'])

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
