from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
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
        self.assertEqual(request_response.data['email_delivery'], 'console')
        self.assertRegex(request_response.data['reset_code'], r'^\d{6}$')
        otp = self.user.password_reset_otps.first()

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
