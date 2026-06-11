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
