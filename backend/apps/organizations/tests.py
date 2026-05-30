from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.users.models import User

from .models import Organization, OrganizationMembership


class OrganizationModelTests(SimpleTestCase):
    def user(self, role):
        return User(id=1, email=f'{role}@example.com', full_name=role, role=role)

    def organization(self, created_by):
        return Organization(
            name='Example Organization',
            registration_no='REG-001',
            email='organization@example.com',
            contact_number='+60123456789',
            address='Example address',
            created_by=created_by,
        )

    def test_hr_head_can_create_organization(self):
        organization = self.organization(self.user(User.Role.HR_HEAD))

        organization.clean()

    def test_non_hr_head_cannot_create_organization(self):
        organization = self.organization(self.user(User.Role.RECRUITER))

        with self.assertRaisesMessage(ValidationError, 'Only an HR head can create an organization.'):
            organization.clean()

    def test_team_membership_accepts_matching_organization_role(self):
        user = self.user(User.Role.INTERVIEWER)
        membership = OrganizationMembership(
            organization=self.organization(self.user(User.Role.HR_HEAD)),
            user=user,
            role=OrganizationMembership.Role.INTERVIEWER,
        )

        membership.clean()

    def test_applicant_cannot_be_added_as_team_member(self):
        applicant = self.user(User.Role.APPLICANT)
        membership = OrganizationMembership(
            organization=self.organization(self.user(User.Role.HR_HEAD)),
            user=applicant,
            role=OrganizationMembership.Role.INTERVIEWER,
        )

        with self.assertRaisesMessage(ValidationError, "Membership role must match the user's role."):
            membership.clean()
