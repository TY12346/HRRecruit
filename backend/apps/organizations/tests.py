from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.jobs.models import JobPosting
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

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class OrganizationAPITests(APITestCase):
    def setUp(self):
        self.hr_head = User.objects.create_user(
            email='head@example.com',
            password='StrongPass123!',
            full_name='HR Head',
            role=User.Role.HR_HEAD,
        )
        self.client.force_authenticate(self.hr_head)
        self.organization_payload = {
            'name': 'Example Organization',
            'registration_no': 'REG-001',
            'email': 'organization@example.com',
            'contact_number': '+60123456789',
            'address': 'Example address',
        }

    def create_organization(self):
        return self.client.post(reverse('organization-create'), self.organization_payload, format='json')

    def test_hr_head_can_create_organization_and_becomes_member(self):
        response = self.create_organization()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        organization = Organization.objects.get(created_by=self.hr_head)
        self.assertEqual(organization.status, Organization.Status.ACTIVE)
        self.assertTrue(
            organization.memberships.filter(
                user=self.hr_head,
                role=OrganizationMembership.Role.HR_HEAD,
                status=OrganizationMembership.Status.ACTIVE,
            ).exists()
        )

    def test_non_hr_head_cannot_create_organization(self):
        recruiter = User.objects.create_user(
            email='recruiter@example.com',
            password='StrongPass123!',
            full_name='Recruiter',
            role=User.Role.RECRUITER,
        )
        self.client.force_authenticate(recruiter)

        response = self.client.post(reverse('organization-create'), self.organization_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hr_head_can_create_search_and_deactivate_team_member(self):
        self.create_organization()
        create_response = self.client.post(
            reverse('organization-member-list-create'),
            {
                'email': 'recruiter@example.com',
                'full_name': 'Recruiter One',
                'phone_number': '+60111111111',
                'role': User.Role.RECRUITER,
            },
            format='json',
        )
        membership_id = create_response.data['member']['id']

        search_response = self.client.get(reverse('organization-member-list-create'), {'search': 'Recruiter One'})
        deactivate_response = self.client.patch(reverse('organization-member-deactivate', args=[membership_id]))

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(search_response.data), 1)
        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)
        membership = OrganizationMembership.objects.get(id=membership_id)
        self.assertEqual(membership.status, OrganizationMembership.Status.INACTIVE)
        self.assertFalse(membership.user.is_active)

    def test_recruiter_can_list_organization_interviewers_but_cannot_create_members(self):
        self.create_organization()
        organization = Organization.objects.get(created_by=self.hr_head)
        recruiter = User.objects.create_user(
            email='list-recruiter@example.com',
            password='StrongPass123!',
            full_name='List Recruiter',
            role=User.Role.RECRUITER,
        )
        interviewer = User.objects.create_user(
            email='list-interviewer@example.com',
            password='StrongPass123!',
            full_name='List Interviewer',
            role=User.Role.INTERVIEWER,
        )
        OrganizationMembership.objects.create(
            organization=organization,
            user=recruiter,
            role=OrganizationMembership.Role.RECRUITER,
        )
        OrganizationMembership.objects.create(
            organization=organization,
            user=interviewer,
            role=OrganizationMembership.Role.INTERVIEWER,
        )
        self.client.force_authenticate(recruiter)

        list_response = self.client.get(reverse('organization-member-list-create'))
        create_response = self.client.post(
            reverse('organization-member-list-create'),
            {
                'email': 'new-interviewer@example.com',
                'full_name': 'New Interviewer',
                'role': User.Role.INTERVIEWER,
            },
            format='json',
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        interviewer_rows = [member for member in list_response.data if member['role'] == User.Role.INTERVIEWER]
        self.assertEqual(len(interviewer_rows), 1)
        self.assertEqual(interviewer_rows[0]['user_id'], interviewer.id)
        self.assertEqual(interviewer_rows[0]['email'], interviewer.email)

    def test_hr_head_can_bulk_import_papaparse_sheetjs_rows_and_receive_row_errors(self):
        self.create_organization()
        payload = {
            'members': [
                {
                    'email': 'interviewer@example.com',
                    'full_name': 'Interviewer One',
                    'phone_number': '',
                    'role': 'interviewer',
                },
                {
                    'email': 'invalid@example.com',
                    'full_name': 'Invalid Role',
                    'phone_number': '',
                    'role': 'applicant',
                },
            ]
        }

        response = self.client.post(reverse('organization-member-bulk-import'), payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Spreadsheet import completed.')
        self.assertEqual(len(response.data['created']), 1)
        self.assertEqual(response.data['created'][0]['role'], User.Role.INTERVIEWER)
        self.assertEqual(response.data['errors'][0]['row'], 3)

    def test_hr_head_cannot_deactivate_member_from_another_organization(self):
        self.create_organization()
        other_head = User.objects.create_user(
            email='other-head@example.com',
            password='StrongPass123!',
            full_name='Other HR Head',
            role=User.Role.HR_HEAD,
        )
        other_organization = Organization.objects.create(
            name='Other Organization',
            registration_no='REG-002',
            email='other@example.com',
            contact_number='+60222222222',
            address='Other address',
            status=Organization.Status.ACTIVE,
            created_by=other_head,
        )
        other_recruiter = User.objects.create_user(
            email='other-recruiter@example.com',
            password='StrongPass123!',
            full_name='Other Recruiter',
            role=User.Role.RECRUITER,
        )
        other_membership = OrganizationMembership.objects.create(
            organization=other_organization,
            user=other_recruiter,
            role=OrganizationMembership.Role.RECRUITER,
        )

        response = self.client.patch(reverse('organization-member-deactivate', args=[other_membership.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        other_membership.refresh_from_db()
        other_recruiter.refresh_from_db()
        self.assertEqual(other_membership.status, OrganizationMembership.Status.ACTIVE)
        self.assertTrue(other_recruiter.is_active)

    def test_delete_soft_deactivates_organization_memberships_and_team_users(self):
        self.create_organization()
        organization = Organization.objects.get(created_by=self.hr_head)
        recruiter = User.objects.create_user(
            email='delete-recruiter@example.com',
            password='StrongPass123!',
            full_name='Delete Recruiter',
            role=User.Role.RECRUITER,
        )
        OrganizationMembership.objects.create(
            organization=organization,
            user=recruiter,
            role=OrganizationMembership.Role.RECRUITER,
        )

        response = self.client.delete(reverse('organization-detail'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        organization.refresh_from_db()
        recruiter.refresh_from_db()
        self.assertEqual(organization.status, Organization.Status.DELETED)
        self.assertFalse(organization.memberships.filter(status=OrganizationMembership.Status.ACTIVE).exists())
        self.assertFalse(recruiter.is_active)
        self.hr_head.refresh_from_db()
        self.assertTrue(self.hr_head.is_active)

    def test_delete_is_blocked_when_active_job_postings_exist(self):
        self.create_organization()
        organization = Organization.objects.get(created_by=self.hr_head)
        recruiter = User.objects.create_user(
            email='job-recruiter@example.com',
            password='StrongPass123!',
            full_name='Job Recruiter',
            role=User.Role.RECRUITER,
        )
        OrganizationMembership.objects.create(
            organization=organization,
            user=recruiter,
            role=OrganizationMembership.Role.RECRUITER,
        )
        JobPosting.objects.create(
            organization=organization,
            recruiter=recruiter,
            title='Software Engineer',
            description='Build recruitment software.',
            employment_type='Full time',
            approximate_salary='5000.00',
            location='Remote',
            status=JobPosting.Status.OPEN,
        )

        response = self.client.delete(reverse('organization-detail'))

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['detail'], 'Organization cannot be deleted yet.')
        self.assertIn('Close all draft or open job postings before deleting the organization.', response.data['blockers'])
        organization.refresh_from_db()
        self.assertEqual(organization.status, Organization.Status.ACTIVE)
        self.assertTrue(organization.memberships.filter(status=OrganizationMembership.Status.ACTIVE).exists())
