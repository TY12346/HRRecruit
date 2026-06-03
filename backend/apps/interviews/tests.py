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

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from tempfile import TemporaryDirectory

from apps.evaluations.models import InterviewAISummary, InterviewEvaluation, InterviewRecording, InterviewTranscript
from apps.jobs.models import EvaluationCriterion, InterviewEvaluationForm


class InterviewEvaluationAPITests(APITestCase):
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
        self.hr_head = self.create_user('eval-head@example.com', User.Role.HR_HEAD)
        self.recruiter = self.create_user('eval-recruiter@example.com', User.Role.RECRUITER)
        self.interviewer = self.create_user('eval-interviewer@example.com', User.Role.INTERVIEWER)
        self.other_interviewer = self.create_user('eval-other-interviewer@example.com', User.Role.INTERVIEWER)
        self.applicant = self.create_user('eval-applicant@example.com', User.Role.APPLICANT)
        self.organization = self.create_organization('Evaluation Organization', self.hr_head, registration_no='REG-EVAL')
        self.other_organization = self.create_organization('Other Evaluation Organization', self.hr_head, registration_no='REG-EVAL-OTHER')
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
        self.form = InterviewEvaluationForm.objects.create(job=self.job, title='Technical Interview')
        self.criterion_one = EvaluationCriterion.objects.create(
            form=self.form,
            criterion_name='Technical Skills',
            description='Evaluate technical problem solving.',
            max_score='10.00',
            weight_score='0.60',
        )
        self.criterion_two = EvaluationCriterion.objects.create(
            form=self.form,
            criterion_name='Communication',
            description='Evaluate communication clarity.',
            max_score='10.00',
            weight_score='0.40',
        )
        self.assign_interviewer()
        self.interview = Interview.objects.get(application=self.application)


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

    def audio_file(self, name='interview.mp3', content_type='audio/mpeg', content=b'mock audio bytes'):
        return SimpleUploadedFile(name, content, content_type=content_type)

    def upload_recording(self):
        self.authenticate(self.interviewer)
        return self.client.post(
            reverse('interview-recording-upload', args=[self.interview.id]),
            {'audio_file': self.audio_file()},
            format='multipart',
        )

    def test_assigned_interviewer_can_upload_transcribe_generate_and_edit_summary(self):
        upload_response = self.upload_recording()
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        recording = InterviewRecording.objects.get(id=upload_response.data['id'])
        self.assertEqual(recording.uploaded_by, self.interviewer)

        transcribe_response = self.client.post(reverse('recording-transcribe', args=[recording.id]))
        self.assertEqual(transcribe_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(transcribe_response.data['transcript_text'], 'This is a mock transcript for FYP development.')
        transcript = InterviewTranscript.objects.get(id=transcribe_response.data['id'])

        summary_response = self.client.post(reverse('transcript-generate-summary', args=[transcript.id]))
        self.assertEqual(summary_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('strengths', summary_response.data)
        summary = InterviewAISummary.objects.get(id=summary_response.data['id'])

        edit_response = self.client.patch(
            reverse('interview-summary-update', args=[summary.id]),
            {'overall_impression': 'Edited interviewer impression.', 'communication_score': '9.00'},
            format='json',
        )
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK)
        summary.refresh_from_db()
        self.assertEqual(summary.overall_impression, 'Edited interviewer impression.')
        self.assertEqual(summary.edited_by, self.interviewer)

    def test_unassigned_interviewer_cannot_upload_recording(self):
        self.authenticate(self.other_interviewer)

        response = self.client.post(
            reverse('interview-recording-upload', args=[self.interview.id]),
            {'audio_file': self.audio_file()},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_audio_upload_validates_file_type(self):
        self.authenticate(self.interviewer)

        response = self.client.post(
            reverse('interview-recording-upload', args=[self.interview.id]),
            {'audio_file': self.audio_file(name='notes.txt', content_type='text/plain')},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('audio_file', response.data)


    def test_audio_upload_validates_file_size(self):
        self.authenticate(self.interviewer)
        oversized_audio = self.audio_file(content=b'x' * (51 * 1024 * 1024))

        response = self.client.post(
            reverse('interview-recording-upload', args=[self.interview.id]),
            {'audio_file': oversized_audio},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('audio_file', response.data)

    def test_interviewer_submits_evaluation_and_recruiter_views_detail(self):
        self.authenticate(self.interviewer)
        response = self.client.post(
            reverse('interview-evaluation-submit', args=[self.interview.id]),
            {
                'overall_comment': 'Strong candidate for the role.',
                'answers': [
                    {'criterion_id': self.criterion_one.id, 'score': '8.00', 'comment': 'Solid API knowledge.'},
                    {'criterion_id': self.criterion_two.id, 'score': '9.00', 'comment': 'Clear communication.'},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        evaluation = InterviewEvaluation.objects.get(id=response.data['id'])
        self.assertEqual(str(evaluation.total_score), '8.40')
        self.application.refresh_from_db()
        self.interview.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.EVALUATION_SUBMITTED)
        self.assertEqual(self.interview.status, Interview.Status.COMPLETED)

        self.authenticate(self.recruiter)
        detail_response = self.client.get(reverse('interview-evaluation-detail', args=[self.interview.id]))

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['evaluation']['id'], evaluation.id)
        self.assertEqual(len(detail_response.data['evaluation']['answers']), 2)

    def test_evaluation_must_answer_all_job_criteria(self):
        self.authenticate(self.interviewer)

        response = self.client.post(
            reverse('interview-evaluation-submit', args=[self.interview.id]),
            {
                'overall_comment': 'Incomplete rubric.',
                'answers': [
                    {'criterion_id': self.criterion_one.id, 'score': '8.00'},
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('answers', response.data)
