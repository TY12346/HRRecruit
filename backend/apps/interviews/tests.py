from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.interviews.models import CalendarEvent, Interview, InterviewInvitation, InterviewStatusHistory
from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


class InterviewManagementAPITests(APITestCase):
    def setUp(self):
        self.hr_head = self.create_user('head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('recruiter@example.com', User.Role.RECRUITER)
        self.interviewer = self.create_user('interviewer@example.com', User.Role.INTERVIEWER)
        self.other_interviewer = self.create_user('other-interviewer@example.com', User.Role.INTERVIEWER)
        self.applicant = self.create_user('applicant@example.com', User.Role.APPLICANT)
        self.other_applicant = self.create_user('other-applicant@example.com', User.Role.APPLICANT)
        self.organization = self.create_organization('Example Organization', self.hr_head)
        self.other_organization = self.create_organization('Other Organization', self.hr_head, registration_no='REG-OTHER')
        self.create_membership(self.hr_head, self.organization, OrganizationMembership.Role.HR_HEAD)
        self.create_membership(self.recruiter, self.organization, OrganizationMembership.Role.RECRUITER)
        self.create_membership(self.interviewer, self.organization, OrganizationMembership.Role.INTERVIEWER)
        self.create_membership(self.other_interviewer, self.other_organization, OrganizationMembership.Role.INTERVIEWER)
        self.job = self.create_job(self.recruiter, self.organization)
        self.application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            status=JobApplication.Status.SHORTLISTED,
        )

    def create_user(self, email, role):
        return User.objects.create_user(email=email, password='test-pass-123', full_name=email, role=role)

    def create_organization(self, name, hr_head, registration_no='REG-EXAMPLE'):
        return Organization.objects.create(
            name=name,
            registration_no=registration_no,
            email=f'{registration_no.lower()}@example.com',
            contact_number='+60123456789',
            address='Example address',
            status=Organization.Status.ACTIVE,
            created_by=hr_head,
        )

    def create_membership(self, user, organization, role):
        return OrganizationMembership.objects.create(organization=organization, user=user, role=role)

    def create_job(self, recruiter, organization):
        return JobPosting.objects.create(
            organization=organization,
            recruiter=recruiter,
            title='Backend Engineer',
            description='Build APIs',
            employment_type='Full-time',
            approximate_salary='5000.00',
            location='Kuala Lumpur',
            status=JobPosting.Status.OPEN,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def assign_interviewer(self):
        self.authenticate(self.recruiter)
        return self.client.post(
            reverse('application-assign-interviewer', args=[self.application.id]),
            {'interviewer_id': self.interviewer.id},
            format='json',
        )

    def send_invitation(self, interview):
        self.authenticate(self.interviewer)
        return self.client.post(
            reverse('interview-send-invitation', args=[interview.id]),
            {
                'proposed_datetime': '2026-07-01T10:00:00Z',
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/interview-1',
            },
            format='json',
        )

    def test_recruiter_assigns_interviewer_from_same_organization(self):
        self.authenticate(self.recruiter)

        external_response = self.client.post(
            reverse('application-assign-interviewer', args=[self.application.id]),
            {'interviewer_id': self.other_interviewer.id},
            format='json',
        )
        response = self.client.post(
            reverse('application-assign-interviewer', args=[self.application.id]),
            {'interviewer_id': self.interviewer.id},
            format='json',
        )

        self.assertEqual(external_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.application.refresh_from_db()
        self.assertEqual(self.application.assigned_interviewer, self.interviewer)
        interview = Interview.objects.get(application=self.application)
        self.assertEqual(interview.organization, self.organization)
        self.assertEqual(interview.interviewer, self.interviewer)

    def test_assigned_interviewer_can_view_assigned_interviews_only(self):
        self.assign_interviewer()
        other_interview = Interview.objects.create(
            application=JobApplication.objects.create(job=self.job, applicant=self.other_applicant),
            organization=self.organization,
            recruiter=self.recruiter,
            interviewer=None,
        )
        self.authenticate(self.interviewer)

        response = self.client.get(reverse('interview-assigned-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        interview_ids = {interview['id'] for interview in response.data}
        self.assertIn(Interview.objects.get(application=self.application).id, interview_ids)
        self.assertNotIn(other_interview.id, interview_ids)

    def test_interviewer_sends_invitation_and_applicant_accepts_with_calendar_placeholder(self):
        self.assign_interviewer()
        interview = Interview.objects.get(application=self.application)

        invitation_response = self.send_invitation(interview)
        self.assertEqual(invitation_response.status_code, status.HTTP_201_CREATED)
        invitation = InterviewInvitation.objects.get(id=invitation_response.data['id'])
        interview.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(interview.status, Interview.Status.INVITATION_SENT)
        self.assertEqual(self.application.status, JobApplication.Status.INTERVIEW_INVITED)
        self.assertTrue(InterviewStatusHistory.objects.filter(interview=interview, to_status=Interview.Status.INVITATION_SENT).exists())
        self.assertTrue(ApplicationStageHistory.objects.filter(application=self.application, to_stage=JobApplication.Status.INTERVIEW_INVITED).exists())

        self.authenticate(self.applicant)
        list_response = self.client.get(reverse('interview-invitation-list'))
        accept_response = self.client.post(reverse('interview-invitation-accept', args=[invitation.id]))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        interview.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(invitation.status, InterviewInvitation.Status.ACCEPTED)
        self.assertIsNotNone(invitation.responded_at)
        self.assertEqual(interview.status, Interview.Status.SCHEDULED)
        self.assertEqual(interview.scheduled_datetime, invitation.proposed_datetime)
        self.assertEqual(self.application.status, JobApplication.Status.INTERVIEW_ACCEPTED)
        self.assertTrue(CalendarEvent.objects.filter(interview=interview, calendar_link__startswith='https://calendar.hrrecruit.local/events/').exists())
        self.assertTrue(accept_response.data['calendar_link'].startswith('https://calendar.hrrecruit.local/events/'))

    def test_applicant_declines_invitation_with_reason(self):
        self.assign_interviewer()
        interview = Interview.objects.get(application=self.application)
        invitation_response = self.send_invitation(interview)
        invitation = InterviewInvitation.objects.get(id=invitation_response.data['id'])
        self.authenticate(self.applicant)

        response = self.client.post(
            reverse('interview-invitation-decline', args=[invitation.id]),
            {'decline_reason': 'I am unavailable at that time.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        interview.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(invitation.status, InterviewInvitation.Status.DECLINED)
        self.assertEqual(invitation.decline_reason, 'I am unavailable at that time.')
        self.assertEqual(interview.status, Interview.Status.DECLINED)
        self.assertEqual(self.application.status, JobApplication.Status.INTERVIEW_DECLINED)
        self.assertTrue(InterviewStatusHistory.objects.filter(interview=interview, to_status=Interview.Status.DECLINED).exists())

    def test_applicant_cannot_respond_to_another_applicants_invitation(self):
        self.assign_interviewer()
        interview = Interview.objects.get(application=self.application)
        invitation_response = self.send_invitation(interview)
        self.authenticate(self.other_applicant)

        response = self.client.post(reverse('interview-invitation-accept', args=[invitation_response.data['id']]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
