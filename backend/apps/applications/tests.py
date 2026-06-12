from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from docx import Document

from apps.jobs.models import JobPosting, JobRequirement
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import ApplicationStageHistory, JobApplication


class JobApplicationAPITests(APITestCase):
    def setUp(self):
        self.hr_head = self.create_user('head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('recruiter@example.com', User.Role.RECRUITER)
        self.other_recruiter = self.create_user('other-recruiter@example.com', User.Role.RECRUITER)
        self.interviewer = self.create_user('interviewer@example.com', User.Role.INTERVIEWER)
        self.external_interviewer = self.create_user('external-interviewer@example.com', User.Role.INTERVIEWER)
        self.applicant = self.create_user('applicant@example.com', User.Role.APPLICANT)
        self.other_applicant = self.create_user('other-applicant@example.com', User.Role.APPLICANT)
        self.organization = self.create_organization('Example Organization', self.hr_head)
        self.create_membership(self.hr_head, self.organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.create_membership(self.other_recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.create_membership(self.interviewer, self.organization, OrganizationMembership.Role.INTERVIEWER)
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

    def test_recruiter_views_ranked_candidates_for_own_job_only(self):
        high_score_application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            final_score='91.25',
        )
        low_score_application = JobApplication.objects.create(
            job=self.job,
            applicant=self.other_applicant,
            final_score='64.50',
        )
        colleague_job = self.create_job(self.other_recruiter, title='Designer')
        JobApplication.objects.create(job=colleague_job, applicant=self.create_user('third@example.com', User.Role.APPLICANT), final_score='99.00')
        self.authenticate(self.recruiter)

        response = self.client.get(reverse('job-ranked-candidates', args=[self.job.id]))
        forbidden_response = self.client.get(reverse('job-ranked-candidates', args=[colleague_job.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [high_score_application.id, low_score_application.id])
        self.assertEqual(forbidden_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ranked_candidates_use_earliest_application_as_equal_score_tie_breaker_and_nulls_last(self):
        newest_equal_score_application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            final_score='80.00',
        )
        oldest_equal_score_application = JobApplication.objects.create(
            job=self.job,
            applicant=self.other_applicant,
            final_score='80.00',
        )
        top_score_application = JobApplication.objects.create(
            job=self.job,
            applicant=self.create_user('top-score@example.com', User.Role.APPLICANT),
            final_score='90.00',
        )
        unscored_application = JobApplication.objects.create(
            job=self.job,
            applicant=self.create_user('unscored@example.com', User.Role.APPLICANT),
            final_score=None,
        )
        base_time = timezone.now() - timezone.timedelta(days=4)
        JobApplication.objects.filter(id=oldest_equal_score_application.id).update(applied_at=base_time)
        JobApplication.objects.filter(id=newest_equal_score_application.id).update(applied_at=base_time + timezone.timedelta(days=2))
        JobApplication.objects.filter(id=top_score_application.id).update(applied_at=base_time + timezone.timedelta(days=3))
        JobApplication.objects.filter(id=unscored_application.id).update(applied_at=base_time - timezone.timedelta(days=1))
        self.authenticate(self.recruiter)

        response = self.client.get(reverse('job-ranked-candidates', args=[self.job.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item['id'] for item in response.data],
            [
                top_score_application.id,
                oldest_equal_score_application.id,
                newest_equal_score_application.id,
                unscored_application.id,
            ],
        )

    def test_recruiter_views_candidate_profile_with_resume_info_scores_and_status(self):
        application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            extracted_skills=['python', 'django'],
            extracted_experience={'years': 4},
            extracted_education={'level': 'bachelor'},
            semantic_score='80.00',
            skill_score='90.00',
            experience_score='70.00',
            education_score='100.00',
            final_score='83.00',
        )
        self.authenticate(self.recruiter)

        response = self.client.get(reverse('application-candidate-profile', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['applicant_profile']['email'], self.applicant.email)
        self.assertEqual(response.data['resume_info']['extracted_experience'], {'years': 4})
        self.assertEqual(response.data['extracted_skills'], ['python', 'django'])
        self.assertEqual(response.data['scores']['final_score'], '83.00')
        self.assertEqual(response.data['status'], JobApplication.Status.SUBMITTED)

    def test_shortlist_requires_same_organization_interviewer_and_records_history(self):
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        other_head = self.create_user('external-head@example.com', User.Role.HR_HEAD)
        other_organization = self.create_organization('External Organization', other_head)
        self.create_membership(other_head, other_organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.external_interviewer, other_organization, OrganizationMembership.Role.INTERVIEWER)
        self.authenticate(self.recruiter)

        invalid_response = self.client.post(
            reverse('application-shortlist', args=[application.id]),
            {'interviewer_id': self.external_interviewer.id, 'remark': 'Strong backend candidate.'},
            format='json',
        )
        valid_response = self.client.post(
            reverse('application-shortlist', args=[application.id]),
            {'interviewer_id': self.interviewer.id, 'remark': 'Strong backend candidate.'},
            format='json',
        )

        self.assertEqual(invalid_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(valid_response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, JobApplication.Status.SHORTLISTED)
        self.assertEqual(application.assigned_interviewer, self.interviewer)
        self.assertEqual(application.recruiter_remark, 'Strong backend candidate.')
        history = application.stage_history.get()
        self.assertEqual(history.from_stage, JobApplication.Status.SUBMITTED)
        self.assertEqual(history.to_stage, JobApplication.Status.SHORTLISTED)
        self.assertEqual(history.changed_by, self.recruiter)

    def test_reject_requires_reason_or_remark_and_records_history(self):
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.recruiter)

        invalid_response = self.client.post(reverse('application-reject', args=[application.id]), {}, format='json')
        valid_response = self.client.post(
            reverse('application-reject', args=[application.id]),
            {'reason': 'Does not meet minimum Django experience.'},
            format='json',
        )

        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(valid_response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, JobApplication.Status.REJECTED)
        self.assertEqual(application.recruiter_remark, 'Does not meet minimum Django experience.')
        history = application.stage_history.get()
        self.assertEqual(history.to_stage, JobApplication.Status.REJECTED)
        self.assertEqual(history.note, 'Does not meet minimum Django experience.')

    def test_remark_is_saved_without_status_change_and_visible_on_candidate_profile(self):
        application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            status=JobApplication.Status.SHORTLISTED,
            assigned_interviewer=self.interviewer,
        )
        self.authenticate(self.recruiter)

        response = self.client.patch(
            reverse('application-remark', args=[application.id]),
            {'remark': 'Ask about API security experience.'},
            format='json',
        )
        profile_response = self.client.get(reverse('application-candidate-profile', args=[application.id]))
        self.authenticate(self.interviewer)
        interviewer_profile_response = self.client.get(reverse('application-candidate-profile', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, JobApplication.Status.SHORTLISTED)
        self.assertEqual(application.recruiter_remark, 'Ask about API security experience.')
        self.assertEqual(profile_response.data['recruiter_remark'], 'Ask about API security experience.')
        self.assertEqual(interviewer_profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(interviewer_profile_response.data['recruiter_remark'], 'Ask about API security experience.')
        history = application.stage_history.get()
        self.assertEqual(history.from_stage, JobApplication.Status.SHORTLISTED)
        self.assertEqual(history.to_stage, JobApplication.Status.SHORTLISTED)


class ApplicationResumeScreeningAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_directory = TemporaryDirectory()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_directory.name)
        cls.media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.media_override.disable()
        cls.media_directory.cleanup()

    def setUp(self):
        self.hr_head = self.create_user('screen-head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('screen-recruiter@example.com', User.Role.RECRUITER)
        self.other_recruiter = self.create_user('screen-other-recruiter@example.com', User.Role.RECRUITER)
        self.applicant = self.create_user('screen-applicant@example.com', User.Role.APPLICANT)
        self.organization = Organization.objects.create(
            name='Screening Organization',
            registration_no='REG-SCREENING',
            email='screening-organization@example.com',
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
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.other_recruiter,
            role=OrganizationMembership.Role.RECRUITER,
        )
        self.job = JobPosting.objects.create(
            organization=self.organization,
            recruiter=self.recruiter,
            title='Backend Engineer',
            description='Build APIs',
            employment_type='Full-time',
            approximate_salary='5000.00',
            location='Kuala Lumpur',
            status=JobPosting.Status.OPEN,
        )

    def create_user(self, email, role):
        return User.objects.create_user(email=email, password='test-pass-123', full_name=email, role=role)

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def create_resume(self, text, filename='resume.docx'):
        output = BytesIO()
        document = Document()
        document.add_paragraph(text)
        document.save(output)
        self.applicant.applicant_profile.resume_file.save(
            filename,
            SimpleUploadedFile(filename, output.getvalue()),
        )

    def test_recruiter_downloads_candidate_resume_through_authenticated_endpoint(self):
        self.create_resume('Python and Django developer resume.')
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.recruiter)

        response = self.client.get(reverse('application-resume', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resume.docx', response.headers['Content-Disposition'])
        self.assertGreater(len(b''.join(response.streaming_content)), 0)

    def test_non_owner_recruiter_cannot_download_candidate_resume(self):
        self.create_resume('Python and Django developer resume.')
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.other_recruiter)

        response = self.client.get(reverse('application-resume', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def create_screening_requirements(self):
        JobRequirement.objects.create(
            job=self.job,
            requirement_type=JobRequirement.RequirementType.SKILL,
            description='Python and Django',
            weight_score='30.00',
            minimum_threshold='60.00',
        )
        JobRequirement.objects.create(
            job=self.job,
            requirement_type=JobRequirement.RequirementType.EXPERIENCE,
            description='At least 3 years of professional experience',
            weight_score='20.00',
            minimum_threshold='60.00',
        )
        JobRequirement.objects.create(
            job=self.job,
            requirement_type=JobRequirement.RequirementType.EDUCATION,
            description="Bachelor's degree",
            weight_score='10.00',
            minimum_threshold='60.00',
        )

    @patch('apps.ai_services.resume_screening.semantic_similarity', return_value=80.0)
    def test_job_owner_screens_uploaded_resume_and_persists_qualified_breakdown(self, _semantic_similarity):
        self.create_resume("Bachelor's degree. Python and Django developer with 5 years of experience.")
        self.create_screening_requirements()
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.recruiter)

        response = self.client.post(reverse('application-screen', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, JobApplication.Status.SCREENED_QUALIFIED)
        self.assertEqual(float(application.semantic_score), 80.0)
        self.assertEqual(float(application.skill_score), 100.0)
        self.assertEqual(float(application.experience_score), 100.0)
        self.assertEqual(float(application.education_score), 100.0)
        self.assertEqual(float(application.final_score), 92.0)
        self.assertEqual(application.extracted_skills, ['django', 'python'])
        self.assertEqual(application.extracted_experience['years'], 5.0)
        self.assertIn('years', application.extracted_experience)
        self.assertIn('roles', application.extracted_experience)
        self.assertIn('matched_phrases', application.extracted_experience)
        self.assertEqual(application.extracted_education['level'], 'bachelor')
        self.assertIn('level', application.extracted_education)
        self.assertIn('fields_of_study', application.extracted_education)
        self.assertIn('matched_keywords', application.extracted_education)
        explanation = response.data['score_explanation']
        required_top_level_keys = {
            'formula',
            'semantic_score',
            'skill_score',
            'experience_score',
            'education_score',
            'final_score',
            'matched_skills',
            'missing_skills',
            'education_match',
            'education_gap',
            'experience_match',
            'experience_gap',
            'notes',
        }
        self.assertTrue(required_top_level_keys.issubset(explanation.keys()))
        self.assertEqual(
            explanation['formula'],
            '0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score',
        )
        self.assertEqual(explanation['semantic_score'], 80.0)
        self.assertEqual(explanation['skill_score'], 100.0)
        self.assertEqual(explanation['experience_score'], 100.0)
        self.assertEqual(explanation['education_score'], 100.0)
        self.assertEqual(explanation['final_score'], 92.0)
        self.assertEqual(explanation['matched_skills'], ['django', 'python'])
        self.assertEqual(explanation['missing_skills'], [])
        self.assertTrue(explanation['education_match'])
        self.assertTrue(explanation['experience_match'])
        self.assertIn('semantic', explanation)
        self.assertIn('skills', explanation)
        self.assertIn('experience', explanation)
        self.assertIn('education', explanation)
        self.assertEqual(explanation['skills']['matched'], ['django', 'python'])
        history = application.stage_history.get()
        self.assertEqual(history.from_stage, JobApplication.Status.SUBMITTED)
        self.assertEqual(history.to_stage, JobApplication.Status.SCREENED_QUALIFIED)
        self.assertEqual(history.changed_by, self.recruiter)

    @patch('apps.ai_services.resume_screening.semantic_similarity', return_value=50.0)
    def test_screening_uses_weighted_skill_scoring_from_job_requirements(self, _semantic_similarity):
        self.create_resume('Python developer with 3 years of experience and a Bachelor Degree.')
        JobRequirement.objects.create(
            job=self.job,
            requirement_type=JobRequirement.RequirementType.SKILL,
            description='Python',
            weight_score='80.00',
            minimum_threshold='60.00',
        )
        JobRequirement.objects.create(
            job=self.job,
            requirement_type=JobRequirement.RequirementType.SKILL,
            description='React',
            weight_score='20.00',
            minimum_threshold='60.00',
        )
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.recruiter)

        response = self.client.post(reverse('application-screen', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(float(application.skill_score), 80.0)
        self.assertEqual(response.data['score_explanation']['skill_score'], 80.0)
        self.assertEqual(response.data['score_explanation']['matched_skills'], ['python'])
        self.assertEqual(response.data['score_explanation']['missing_skills'], ['react'])
        self.assertEqual(
            response.data['score_explanation']['skills']['weights'],
            {'python': 80.0, 'react': 20.0},
        )

    @patch('apps.ai_services.resume_screening.semantic_similarity', return_value=0.0)
    def test_low_score_marks_application_not_qualified_without_rejecting_it(self, _semantic_similarity):
        self.create_resume('High school graduate with Java experience.')
        self.create_screening_requirements()
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.recruiter)

        response = self.client.post(reverse('application-screen', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, JobApplication.Status.SCREENED_NOT_QUALIFIED)
        self.assertNotEqual(application.status, JobApplication.Status.REJECTED)
        self.assertEqual(float(application.final_score), 3.33)
        history = application.stage_history.get()
        self.assertEqual(history.to_stage, JobApplication.Status.SCREENED_NOT_QUALIFIED)
        self.assertIn('Recruiter review is still required', history.note)
        self.assertFalse(
            ApplicationStageHistory.objects.filter(
                application=application,
                to_stage=JobApplication.Status.REJECTED,
            ).exists()
        )

    def test_score_explanation_contains_nested_required_sections_for_not_qualified_screening(self):
        self.create_resume('High school graduate with Java experience.')
        self.create_screening_requirements()
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.recruiter)

        with patch('apps.ai_services.resume_screening.semantic_similarity', return_value=0.0):
            response = self.client.post(reverse('application-screen', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        explanation = response.data['score_explanation']
        self.assertEqual(explanation['threshold'], 60.0)
        self.assertEqual(explanation['semantic']['score'], explanation['semantic_score'])
        self.assertEqual(explanation['skills']['score'], explanation['skill_score'])
        self.assertEqual(explanation['experience']['score'], explanation['experience_score'])
        self.assertEqual(explanation['education']['score'], explanation['education_score'])
        self.assertIn('gap', explanation['experience'])
        self.assertIn('gap', explanation['education'])
        self.assertIsInstance(explanation['notes'], list)

    def test_screening_requires_an_uploaded_resume(self):
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.recruiter)

        response = self.client.post(reverse('application-screen', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['resume_file'], 'The applicant must upload a resume before screening.')

    def test_colleague_recruiter_cannot_screen_job_owners_application(self):
        self.create_resume('Python developer')
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.other_recruiter)

        response = self.client.post(reverse('application-screen', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        application.refresh_from_db()
        self.assertEqual(application.status, JobApplication.Status.SUBMITTED)

    def test_non_recruiter_cannot_screen_an_application(self):
        application = JobApplication.objects.create(job=self.job, applicant=self.applicant)
        self.authenticate(self.hr_head)

        response = self.client.post(reverse('application-screen', args=[application.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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
