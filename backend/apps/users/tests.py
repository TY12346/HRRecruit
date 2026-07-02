import os
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User
from .permissions import (
    IsApplicant,
    IsHRHead,
    IsInterviewer,
    IsOrganizationMember,
    IsRecruiter,
    IsRecruiterOrHRHead,
)


class RolePermissionTests(SimpleTestCase):
    def request_for(self, role):
        return SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role=role))

    def assert_allowed_roles(self, permission_class, allowed_roles):
        permission = permission_class()
        for role in User.Role.values:
            with self.subTest(permission=permission_class.__name__, role=role):
                self.assertEqual(
                    permission.has_permission(self.request_for(role), view=None),
                    role in allowed_roles,
                )

    def test_role_specific_permissions_only_allow_their_corresponding_role(self):
        permission_roles = (
            (IsApplicant, {User.Role.APPLICANT}),
            (IsRecruiter, {User.Role.RECRUITER}),
            (IsInterviewer, {User.Role.INTERVIEWER}),
            (IsHRHead, {User.Role.HR_HEAD}),
        )

        for permission_class, allowed_roles in permission_roles:
            self.assert_allowed_roles(permission_class, allowed_roles)

    def test_recruiter_or_hr_head_permission_allows_both_roles(self):
        self.assert_allowed_roles(
            IsRecruiterOrHRHead,
            {User.Role.RECRUITER, User.Role.HR_HEAD},
        )

    def test_organization_member_permission_excludes_applicants(self):
        self.assert_allowed_roles(
            IsOrganizationMember,
            {User.Role.RECRUITER, User.Role.INTERVIEWER, User.Role.HR_HEAD},
        )

    def test_permissions_reject_anonymous_users(self):
        request = SimpleNamespace(user=AnonymousUser())
        permission_classes = (
            IsApplicant,
            IsRecruiter,
            IsInterviewer,
            IsHRHead,
            IsRecruiterOrHRHead,
            IsOrganizationMember,
        )

        for permission_class in permission_classes:
            with self.subTest(permission=permission_class.__name__):
                self.assertFalse(permission_class().has_permission(request, view=None))


class RegistrationAPITests(APITestCase):
    def test_public_registration_creates_hr_head_account_only(self):
        response = self.client.post(
            reverse('auth-register'),
            {
                'email': 'head@example.com',
                'full_name': 'HR Department Head',
                'phone_number': '+60123456789',
                'password': 'StrongPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], User.Role.HR_HEAD)

        user = User.objects.get(email='head@example.com')
        self.assertEqual(user.role, User.Role.HR_HEAD)
        self.assertTrue(hasattr(user, 'hr_head_profile'))
        self.assertFalse(hasattr(user, 'applicant_profile'))

    def test_applicant_registration_endpoint_creates_applicant_for_mobile_app(self):
        response = self.client.post(
            reverse('auth-register-applicant'),
            {
                'email': 'applicant@example.com',
                'full_name': 'Job Applicant',
                'phone_number': '+60123456789',
                'password': 'StrongPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], User.Role.APPLICANT)

        user = User.objects.get(email='applicant@example.com')
        self.assertEqual(user.role, User.Role.APPLICANT)
        self.assertTrue(hasattr(user, 'applicant_profile'))
        self.assertFalse(hasattr(user, 'hr_head_profile'))

    def test_applicant_registration_can_recover_mobile_created_hr_head_without_organization(self):
        mistaken_user = User.objects.create_user(
            email='mistaken-mobile@example.com',
            password='StrongPass123!',
            full_name='Mistaken HR Head',
            role=User.Role.HR_HEAD,
        )
        self.assertTrue(hasattr(mistaken_user, 'hr_head_profile'))

        response = self.client.post(
            reverse('auth-register-applicant'),
            {
                'email': 'mistaken-mobile@example.com',
                'full_name': 'Recovered Applicant',
                'phone_number': '+60999999999',
                'password': 'StrongPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mistaken_user.refresh_from_db()
        self.assertEqual(mistaken_user.role, User.Role.APPLICANT)
        self.assertEqual(mistaken_user.full_name, 'Recovered Applicant')
        self.assertTrue(hasattr(mistaken_user, 'applicant_profile'))
        self.assertFalse(hasattr(mistaken_user, 'hr_head_profile'))
        self.assertEqual(response.data['user']['role'], User.Role.APPLICANT)

class PasswordManagementAPITests(APITestCase):
    def setUp(self):
        self.email_patcher = patch(
            'apps.users.serializers.send_password_reset_otp_email',
            return_value={'provider': 'sendgrid', 'status_code': 202},
        )
        self.email_patcher.start()
        self.addCleanup(self.email_patcher.stop)
        self.user = User.objects.create_user(
            email='password-user@example.com',
            password='OldPass123!',
            full_name='Password User',
            role=User.Role.APPLICANT,
        )
        self.staff_user = User.objects.create_user(
            email='staff-password@example.com',
            password='OldPass123!',
            full_name='Staff Password User',
            role=User.Role.RECRUITER,
        )

    def test_authenticated_user_can_change_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse('auth-password-change'),
            {
                'current_password': 'OldPass123!',
                'new_password': 'NewPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_change_password_requires_correct_current_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse('auth-password-change'),
            {
                'current_password': 'WrongPass123!',
                'new_password': 'NewPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))

    def test_password_reset_otp_flow_sets_new_password(self):
        request_response = self.client.post(
            reverse('auth-password-reset-request'),
            {'email': self.user.email.upper(), 'client_app': 'mobile'},
            format='json',
        )
        self.assertEqual(request_response.status_code, status.HTTP_200_OK)
        self.assertEqual(request_response.data['email_delivery'], 'sendgrid')
        self.assertNotIn('reset_code', request_response.data)
        otp = self.user.password_reset_otps.first()

        verify_response = self.client.post(
            reverse('auth-password-reset-verify'),
            {
                'email': self.user.email.upper(),
                'client_app': 'mobile',
                'otp_code': otp.otp_code,
            },
            format='json',
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        confirm_response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'email': self.user.email.upper(),
                'client_app': 'mobile',
                'otp_code': otp.otp_code,
                'new_password': 'ResetPass123!',
            },
            format='json',
        )

        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        otp.refresh_from_db()
        self.assertTrue(self.user.check_password('ResetPass123!'))
        self.assertTrue(otp.is_used)


    def test_password_reset_verify_rejects_wrong_mobile_otp(self):
        self.client.post(
            reverse('auth-password-reset-request'),
            {'email': self.user.email, 'client_app': 'mobile'},
            format='json',
        )

        response = self.client.post(
            reverse('auth-password-reset-verify'),
            {
                'email': self.user.email,
                'client_app': 'mobile',
                'otp_code': '000000',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))

    def test_web_password_reset_does_not_send_for_applicant_accounts(self):
        response = self.client.post(
            reverse('auth-password-reset-request'),
            {'email': self.user.email, 'client_app': 'web'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('reset_code', response.data)
        self.assertFalse(self.user.password_reset_otps.exists())

    def test_mobile_password_reset_does_not_send_for_staff_accounts(self):
        response = self.client.post(
            reverse('auth-password-reset-request'),
            {'email': self.staff_user.email, 'client_app': 'mobile'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('reset_code', response.data)
        self.assertFalse(self.staff_user.password_reset_otps.exists())

    def test_web_password_reset_allows_staff_accounts_without_returning_reset_code(self):
        response = self.client.post(
            reverse('auth-password-reset-request'),
            {'email': self.staff_user.email, 'client_app': 'web'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('reset_code', response.data)
        self.assertNotIn('reset_link', response.data)
        self.assertTrue(self.staff_user.password_reset_otps.exists())

    def test_web_password_reset_confirm_accepts_reset_token_from_email_link(self):
        self.client.post(
            reverse('auth-password-reset-request'),
            {'email': self.staff_user.email, 'client_app': 'web'},
            format='json',
        )
        otp = self.staff_user.password_reset_otps.first()

        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'email': self.staff_user.email,
                'client_app': 'web',
                'reset_token': otp.otp_code,
                'new_password': 'ResetPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.staff_user.refresh_from_db()
        self.assertTrue(self.staff_user.check_password('ResetPass123!'))


class LinkedInProfilePdfImportAPITests(APITestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(
            email='linkedin-applicant@example.com',
            password='StrongPass123!',
            full_name='Old Name',
            role=User.Role.APPLICANT,
        )
        self.recruiter = User.objects.create_user(
            email='linkedin-recruiter@example.com',
            password='StrongPass123!',
            full_name='Recruiter User',
            role=User.Role.RECRUITER,
        )

    @patch('apps.users.views.extract_resume_text')
    def test_applicant_imports_linkedin_pdf_and_profile_is_filled(self, mock_extract_text):
        temporary_paths_seen_by_extractor = []

        def extract_from_closed_temporary_file(path):
            self.assertTrue(os.path.exists(path))
            temporary_paths_seen_by_extractor.append(path)
            return (
                'Jane Candidate\nSenior Django Developer\n'
                'https://www.linkedin.com/in/jane-candidate\n'
                'Experience\n5 years as Software Engineer at ExampleCo\n'
                'Education\nBachelor of Computer Science\n'
                'Skills\nPython Django PostgreSQL REST API\n'
                'Licenses & Certifications\nAWS Certified Cloud Practitioner\n'
            )

        mock_extract_text.side_effect = extract_from_closed_temporary_file
        self.client.force_authenticate(user=self.applicant)

        response = self.client.post(
            reverse('auth-linkedin-profile-import'),
            {
                'linkedin_pdf': SimpleUploadedFile(
                    'linkedin-profile.pdf',
                    b'%PDF-1.4 linked in profile',
                    content_type='application/pdf',
                )
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.full_name, 'Jane Candidate')
        self.assertEqual(
            self.applicant.applicant_profile.linkedin_url,
            'https://www.linkedin.com/in/jane-candidate',
        )
        self.assertIn(
            'Senior Django Developer',
            self.applicant.applicant_profile.personal_summary,
        )
        self.assertIn('Django', response.data['extracted_profile']['skills'])
        self.assertEqual(response.data['user']['full_name'], 'Jane Candidate')
        self.assertEqual(len(temporary_paths_seen_by_extractor), 1)
        self.assertFalse(os.path.exists(temporary_paths_seen_by_extractor[0]))

    def test_non_applicant_cannot_import_linkedin_pdf(self):
        self.client.force_authenticate(user=self.recruiter)

        response = self.client.post(
            reverse('auth-linkedin-profile-import'),
            {
                'linkedin_pdf': SimpleUploadedFile(
                    'linkedin-profile.pdf',
                    b'%PDF-1.4 linked in profile',
                    content_type='application/pdf',
                )
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_linkedin_import_requires_pdf(self):
        self.client.force_authenticate(user=self.applicant)

        response = self.client.post(
            reverse('auth-linkedin-profile-import'),
            {
                'linkedin_pdf': SimpleUploadedFile(
                    'linkedin-profile.txt',
                    b'not a pdf',
                    content_type='text/plain',
                )
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('linkedin_pdf', response.data)


class ApplicantProfileSectionAPITests(APITestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(
            email='section-applicant@example.com',
            password='StrongPass123!',
            full_name='Section Applicant',
            role=User.Role.APPLICANT,
        )

    def test_applicant_can_save_linkedin_style_profile_sections(self):
        self.client.force_authenticate(user=self.applicant)

        response = self.client.patch(
            reverse('auth-profile'),
            {
                'full_name': 'Section Applicant',
                'phone_number': '+60123456789',
                'linkedin_url': 'https://www.linkedin.com/in/section-applicant',
                'personal_summary': 'Backend developer.',
                'experiences': [
                    {
                        'job_title': 'Software Engineer',
                        'employment_type': 'Full-time',
                        'company_name': 'ExampleCo',
                        'start_date': '2024-01-01',
                        'location': 'Kuala Lumpur',
                    }
                ],
                'educations': [
                    {
                        'school_name': 'Example University',
                        'degree_name': 'Bachelor',
                        'field_of_study': 'Computer Science',
                        'start_date': '2020-01-01',
                        'end_date': '2023-12-31',
                        'grade': '3.80',
                    }
                ],
                'skills': [{'skill_name': 'Django'}, {'skill_name': 'Flutter'}],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['experiences'][0]['job_title'], 'Software Engineer')
        self.assertEqual(response.data['user']['educations'][0]['school_name'], 'Example University')
        self.assertEqual(
            sorted(skill['skill_name'] for skill in response.data['user']['skills']),
            ['Django', 'Flutter'],
        )
        self.assertEqual(self.applicant.experiences.count(), 1)
        self.assertEqual(self.applicant.educations.count(), 1)
        self.assertEqual(self.applicant.skills.count(), 2)


class ApplicantResumeLibraryAPITests(APITestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(
            email='resume-applicant@example.com',
            password='StrongPass123!',
            full_name='Resume Applicant',
            role=User.Role.APPLICANT,
        )
        self.recruiter = User.objects.create_user(
            email='resume-recruiter@example.com',
            password='StrongPass123!',
            full_name='Resume Recruiter',
            role=User.Role.RECRUITER,
        )

    def upload_resume(self, filename, title):
        return self.client.post(
            reverse('auth-resumes'),
            {
                'title': title,
                'resume_file': SimpleUploadedFile(filename, b'%PDF-1.4 resume', content_type='application/pdf'),
            },
            format='multipart',
        )

    def test_applicant_can_upload_and_list_multiple_resumes(self):
        self.client.force_authenticate(user=self.applicant)

        first_response = self.upload_resume('backend.pdf', 'Backend resume')
        second_response = self.upload_resume('data.pdf', 'Data resume')
        list_response = self.client.get(reverse('auth-resumes'))

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 2)
        self.assertTrue(first_response.data['resume']['is_default'])
        self.assertFalse(second_response.data['resume']['is_default'])
        self.assertEqual(self.applicant.resumes.count(), 2)


    def test_applicant_cannot_upload_more_than_five_resumes(self):
        self.client.force_authenticate(user=self.applicant)
        for index in range(5):
            response = self.upload_resume(f'resume-{index}.pdf', f'Resume {index}')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.upload_resume('resume-6.pdf', 'Resume 6')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['resumes'][0], 'You can upload a maximum of 5 resumes.')
        self.assertEqual(self.applicant.resumes.count(), 5)

    def test_applicant_can_change_default_resume(self):
        self.client.force_authenticate(user=self.applicant)
        first_response = self.upload_resume('backend.pdf', 'Backend resume')
        second_response = self.upload_resume('data.pdf', 'Data resume')

        response = self.client.patch(
            reverse('auth-resume-detail', args=[second_response.data['resume']['id']]),
            {'is_default': True},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['resume']['is_default'])
        self.applicant.refresh_from_db()
        self.assertTrue(self.applicant.resumes.get(id=second_response.data['resume']['id']).is_default)
        self.assertFalse(self.applicant.resumes.get(id=first_response.data['resume']['id']).is_default)
        self.assertIn('data', self.applicant.applicant_profile.resume_file.name)

    def test_legacy_resume_upload_replaces_default_resume(self):
        self.client.force_authenticate(user=self.applicant)
        first_response = self.upload_resume('backend.pdf', 'Backend resume')

        response = self.client.post(
            reverse('auth-resume-upload'),
            {
                'title': 'Sales resume',
                'resume_file': SimpleUploadedFile(
                    'sales.pdf',
                    b'%PDF-1.4 sales resume',
                    content_type='application/pdf',
                ),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['resume']['is_default'])
        self.applicant.refresh_from_db()
        self.assertIn('sales', self.applicant.applicant_profile.resume_file.name)
        self.assertTrue(self.applicant.resumes.get(id=response.data['resume']['id']).is_default)
        self.assertFalse(self.applicant.resumes.get(id=first_response.data['resume']['id']).is_default)

    def test_non_applicant_cannot_upload_resume(self):
        self.client.force_authenticate(user=self.recruiter)

        response = self.upload_resume('recruiter.pdf', 'Recruiter resume')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
