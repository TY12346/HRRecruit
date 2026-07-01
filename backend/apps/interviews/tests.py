import json
import os
from unittest.mock import patch
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.interviews.models import CalendarEvent, GoogleCalendarCredential, Interview, InterviewSchedulingRequest, InterviewStatusHistory, InterviewerAvailabilitySlot
from apps.interviews.views import bookable_scheduling_requests_for_applicant
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


    def test_google_calendar_status_uses_safe_fallback_when_not_configured(self):
        self.authenticate(self.recruiter)

        with patch.dict('os.environ', {'GOOGLE_CALENDAR_ENABLED': 'false'}, clear=False):
            response = self.client.get(reverse('google-calendar-status'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['connected'])
        self.assertFalse(response.data['oauth_ready'])
        self.assertIn(response.data['fallback_mode'], ['local_placeholder', 'google_template_link'])

    def test_google_calendar_connect_requires_oauth_configuration(self):
        self.authenticate(self.recruiter)

        with patch.dict('os.environ', {'GOOGLE_CALENDAR_ENABLED': 'false'}, clear=False):
            response = self.client.get(reverse('google-calendar-connect'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('google_calendar', response.data)

    def test_google_calendar_connect_returns_clean_error_when_oauth_library_fails(self):
        self.authenticate(self.recruiter)

        with patch(
            'apps.interviews.views.build_google_calendar_authorization_url',
            side_effect=RuntimeError('oauthlib failed'),
        ):
            response = self.client.get(reverse('google-calendar-connect'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('google_calendar', response.data)
        self.assertIn('Unable to start Google Calendar OAuth', response.data['google_calendar'])

    def test_local_http_google_oauth_redirect_sets_oauthlib_debug_escape_hatch(self):
        from apps.interviews.calendar_service import _allow_local_http_oauth_for_debug

        with override_settings(DEBUG=True), patch.dict(
            'os.environ',
            {'GOOGLE_CALENDAR_REDIRECT_URI': 'http://localhost:5173/recruiter/calendar/google/callback'},
            clear=False,
        ):
            os.environ.pop('OAUTHLIB_INSECURE_TRANSPORT', None)
            _allow_local_http_oauth_for_debug()

        self.assertEqual(os.environ.get('OAUTHLIB_INSECURE_TRANSPORT'), '1')

    def test_calendar_sync_falls_back_to_local_event_without_google_oauth(self):
        from apps.interviews.calendar_service import sync_calendar_event_for_interview

        interview = Interview.objects.create(
            application=self.application,
            organization=self.organization,
            recruiter=self.recruiter,
            interviewer=self.interviewer,
            scheduled_datetime='2026-07-09T09:00:00Z',
            interview_date='2026-07-09',
            start_time='09:00:00',
            end_time='10:00:00',
            mode=Interview.Mode.ONLINE,
            meeting_link='https://meet.example.com/fallback',
            status=Interview.Status.SCHEDULED,
        )

        with patch.dict('os.environ', {'GOOGLE_CALENDAR_ENABLED': 'false'}, clear=False):
            event = sync_calendar_event_for_interview(interview)

        self.assertEqual(event.provider, 'local')
        self.assertEqual(event.sync_status, CalendarEvent.SyncStatus.NOT_SYNCED)
        self.assertIn('calendar.hrrecruit.local', event.calendar_link)

    def test_interviewer_creates_availability_slot(self):
        self.authenticate(self.interviewer)

        response = self.client.post(
            reverse('interviewer-availability-list-create'),
            {
                'start_datetime': '2026-07-02T09:00:00Z',
                'end_datetime': '2026-07-02T10:00:00Z',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        slot = InterviewerAvailabilitySlot.objects.get(id=response.data['id'])
        self.assertEqual(slot.organization, self.organization)
        self.assertEqual(slot.interviewer, self.interviewer)
        self.assertEqual(slot.status, InterviewerAvailabilitySlot.Status.AVAILABLE)


    def test_interviewer_duplicate_availability_returns_validation_error(self):
        self.authenticate(self.interviewer)
        payload = {
            'start_datetime': '2026-07-02T09:00:00Z',
            'end_datetime': '2026-07-02T10:00:00Z',
        }

        first_response = self.client.post(reverse('interviewer-availability-list-create'), payload, format='json')
        duplicate_response = self.client.post(reverse('interviewer-availability-list-create'), payload, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_datetime', duplicate_response.data)

    def test_recruiter_creates_scheduling_request_for_applicant(self):
        self.authenticate(self.recruiter)

        response = self.client.post(
            reverse('application-create-scheduling-request', args=[self.application.id]),
            {'interviewer_id': self.interviewer.id, 'remark': 'Please choose a technical interview slot.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        scheduling_request = InterviewSchedulingRequest.objects.get(id=response.data['id'])
        self.assertEqual(scheduling_request.application, self.application)
        self.assertEqual(scheduling_request.organization, self.organization)
        self.assertEqual(scheduling_request.recruiter, self.recruiter)
        self.assertEqual(scheduling_request.interviewer, self.interviewer)
        self.assertEqual(scheduling_request.remark, 'Please choose a technical interview slot.')
        self.assertIsNotNone(scheduling_request.interview)
        self.assertEqual(scheduling_request.interview.interviewer, self.interviewer)
        self.assertEqual(scheduling_request.interview.status, Interview.Status.ASSIGNED)
        self.assertEqual(scheduling_request.interview.scheduling_method, Interview.SchedulingMethod.SELF_SCHEDULED)

        self.authenticate(self.interviewer)
        assigned_response = self.client.get(reverse('interview-assigned-list'))

        self.assertEqual(assigned_response.status_code, status.HTTP_200_OK)
        self.assertIn(scheduling_request.interview.id, {interview['id'] for interview in assigned_response.data})


    def test_booking_lock_queryset_avoids_nullable_select_related_joins(self):
        queryset = bookable_scheduling_requests_for_applicant(self.applicant)

        self.assertNotIn('selected_slot', queryset.query.select_related)
        self.assertNotIn('interview', queryset.query.select_related)
        self.assertIn('application', queryset.query.select_related)
        self.assertIn('organization', queryset.query.select_related)
        self.assertIn('recruiter', queryset.query.select_related)
        self.assertIn('interviewer', queryset.query.select_related)

    def test_applicant_books_available_slot_from_scheduling_request(self):
        slot = InterviewerAvailabilitySlot.objects.create(
            organization=self.organization,
            interviewer=self.interviewer,
            start_datetime='2026-07-03T09:00:00Z',
            end_datetime='2026-07-03T10:00:00Z',
        )
        scheduling_request = InterviewSchedulingRequest.objects.create(
            application=self.application,
            organization=self.organization,
            recruiter=self.recruiter,
            interviewer=self.interviewer,
            remark='Choose one slot.',
        )
        self.authenticate(self.applicant)

        response = self.client.post(
            reverse('interview-scheduling-request-book', args=[scheduling_request.id]),
            {
                'slot_id': slot.id,
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/self-scheduled',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        scheduling_request.refresh_from_db()
        slot.refresh_from_db()
        interview = Interview.objects.get(application=self.application)
        self.assertEqual(scheduling_request.status, InterviewSchedulingRequest.Status.SCHEDULED)
        self.assertEqual(scheduling_request.selected_slot, slot)
        self.assertEqual(scheduling_request.interview, interview)
        self.assertEqual(slot.status, InterviewerAvailabilitySlot.Status.BOOKED)
        self.assertEqual(interview.status, Interview.Status.SCHEDULED)
        self.assertEqual(interview.availability_slot, slot)
        self.assertEqual(interview.scheduling_method, Interview.SchedulingMethod.SELF_SCHEDULED)
        self.assertEqual(interview.meeting_link, 'https://meet.example.com/self-scheduled')
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.INTERVIEW_ACCEPTED)


    def test_applicant_books_slot_from_recruiter_created_scheduling_request(self):
        self.authenticate(self.interviewer)
        slot_response = self.client.post(
            reverse('interviewer-availability-list-create'),
            {
                'start_datetime': '2026-07-05T09:00:00Z',
                'end_datetime': '2026-07-05T10:00:00Z',
            },
            format='json',
        )
        self.assertEqual(slot_response.status_code, status.HTTP_201_CREATED)

        self.authenticate(self.recruiter)
        request_response = self.client.post(
            reverse('application-create-scheduling-request', args=[self.application.id]),
            {'interviewer_id': self.interviewer.id, 'remark': 'Choose a slot.'},
            format='json',
        )
        self.assertEqual(request_response.status_code, status.HTTP_201_CREATED)

        self.authenticate(self.applicant)
        booking_response = self.client.post(
            reverse('interview-scheduling-request-book', args=[request_response.data['id']]),
            {
                'slot_id': slot_response.data['id'],
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/self-scheduled-api',
            },
            format='json',
        )

        self.assertEqual(booking_response.status_code, status.HTTP_200_OK)
        self.assertEqual(booking_response.data['status'], InterviewSchedulingRequest.Status.SCHEDULED)
        self.assertEqual(booking_response.data['selected_slot']['id'], slot_response.data['id'])
        interview = Interview.objects.get(application=self.application)
        self.assertEqual(interview.status, Interview.Status.SCHEDULED)
        self.assertEqual(interview.scheduled_datetime, interview.availability_slot.start_datetime)


    @patch('apps.interviews.views.create_notification')
    @patch('apps.interviews.views.sync_calendar_event_for_interview')
    def test_booking_still_succeeds_when_optional_side_effects_fail(self, sync_calendar_event, create_notification_mock):
        sync_calendar_event.side_effect = RuntimeError('Calendar service unavailable')
        create_notification_mock.side_effect = RuntimeError('Notification service unavailable')
        slot = InterviewerAvailabilitySlot.objects.create(
            organization=self.organization,
            interviewer=self.interviewer,
            start_datetime='2026-07-06T09:00:00Z',
            end_datetime='2026-07-06T10:00:00Z',
        )
        scheduling_request = InterviewSchedulingRequest.objects.create(
            application=self.application,
            organization=self.organization,
            recruiter=self.recruiter,
            interviewer=self.interviewer,
            remark='Choose one slot.',
        )
        self.authenticate(self.applicant)

        response = self.client.post(
            reverse('interview-scheduling-request-book', args=[scheduling_request.id]),
            {
                'slot_id': slot.id,
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/side-effect-failure',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        scheduling_request.refresh_from_db()
        slot.refresh_from_db()
        self.assertEqual(scheduling_request.status, InterviewSchedulingRequest.Status.SCHEDULED)
        self.assertEqual(slot.status, InterviewerAvailabilitySlot.Status.BOOKED)

    def test_applicant_cannot_book_unavailable_slot(self):
        slot = InterviewerAvailabilitySlot.objects.create(
            organization=self.organization,
            interviewer=self.interviewer,
            start_datetime='2026-07-04T09:00:00Z',
            end_datetime='2026-07-04T10:00:00Z',
            status=InterviewerAvailabilitySlot.Status.BOOKED,
        )
        scheduling_request = InterviewSchedulingRequest.objects.create(
            application=self.application,
            organization=self.organization,
            recruiter=self.recruiter,
            interviewer=self.interviewer,
        )
        self.authenticate(self.applicant)

        response = self.client.post(
            reverse('interview-scheduling-request-book', args=[scheduling_request.id]),
            {
                'slot_id': slot.id,
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/unavailable',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Interview.objects.filter(application=self.application).exists())

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


from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from tempfile import TemporaryDirectory
from unittest.mock import patch

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

    def audio_file(self, name='interview.mp3', content_type='audio/mpeg', content=b'audio bytes'):
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

        with patch.dict('os.environ', {'USE_REAL_TRANSCRIPTION': 'True', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.transcription_service._call_openai_transcription',
            return_value='Candidate discussed Django API experience and communicated clearly.',
        ):
            transcribe_response = self.client.post(reverse('recording-transcribe', args=[recording.id]))
        self.assertEqual(transcribe_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(transcribe_response.data['transcript_text'], 'Candidate discussed Django API experience and communicated clearly.')
        self.assertEqual(transcribe_response.data['transcript_json']['provider'], 'openai')
        transcript = InterviewTranscript.objects.get(id=transcribe_response.data['id'])

        with patch.dict('os.environ', {'USE_REAL_SUMMARY': 'True', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.summary_service._call_openai_summary',
            return_value=json.dumps({
                'strengths': 'Strong Django API experience.',
                'weaknesses': 'Needs more detail on testing.',
                'communication_score': 8,
                'overall_impression': 'Clear and relevant interview responses.',
                'editable_summary_text': 'Strong Django API experience with clear communication.',
            }),
        ):
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


    def test_real_transcription_uses_openai_when_enabled_and_configured(self):
        upload_response = self.upload_recording()
        recording = InterviewRecording.objects.get(id=upload_response.data['id'])

        with patch.dict('os.environ', {'USE_REAL_TRANSCRIPTION': 'True', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.transcription_service._call_openai_transcription',
            return_value='Real provider transcript text.',
        ) as openai_transcription:
            response = self.client.post(reverse('recording-transcribe', args=[recording.id]))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['transcript_text'], 'Real provider transcript text.')
        self.assertEqual(response.data['transcript_json']['provider'], 'openai')
        self.assertEqual(response.data['transcript_json']['model'], 'whisper-1')
        self.assertEqual(InterviewTranscript.objects.filter(recording=recording).count(), 1)
        openai_transcription.assert_called_once()

    def test_openai_api_key_alone_returns_clear_transcription_error(self):
        upload_response = self.upload_recording()
        recording = InterviewRecording.objects.get(id=upload_response.data['id'])
        original_flag = os.environ.pop('USE_REAL_TRANSCRIPTION', None)
        try:
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}), patch(
                'apps.ai_services.transcription_service._call_openai_transcription',
                return_value='Real transcript should not be used by key alone.',
            ) as openai_transcription:
                response = self.client.post(reverse('recording-transcribe', args=[recording.id]))
        finally:
            if original_flag is not None:
                os.environ['USE_REAL_TRANSCRIPTION'] = original_flag

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('Real transcription is disabled', str(response.data['detail']))
        openai_transcription.assert_not_called()

    def test_real_transcription_missing_api_key_returns_clear_error(self):
        upload_response = self.upload_recording()
        recording = InterviewRecording.objects.get(id=upload_response.data['id'])

        with patch.dict('os.environ', {'USE_REAL_TRANSCRIPTION': 'True', 'OPENAI_API_KEY': ''}), patch(
            'apps.ai_services.transcription_service._call_openai_transcription'
        ) as openai_transcription:
            response = self.client.post(reverse('recording-transcribe', args=[recording.id]))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('OPENAI_API_KEY is required', str(response.data['detail']))
        openai_transcription.assert_not_called()

    def test_real_transcription_provider_failure_returns_clear_error_without_saving_transcript(self):
        upload_response = self.upload_recording()
        recording = InterviewRecording.objects.get(id=upload_response.data['id'])

        with patch.dict('os.environ', {'USE_REAL_TRANSCRIPTION': 'True', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.transcription_service._call_openai_transcription',
            side_effect=RuntimeError('provider unavailable'),
        ) as openai_transcription:
            response = self.client.post(reverse('recording-transcribe', args=[recording.id]))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('Real transcription failed', str(response.data['detail']))
        self.assertFalse(InterviewTranscript.objects.filter(recording=recording).exists())
        openai_transcription.assert_called_once()

    def test_transcription_response_is_saved_for_existing_evaluation_flow(self):
        upload_response = self.upload_recording()
        recording = InterviewRecording.objects.get(id=upload_response.data['id'])

        with patch.dict('os.environ', {'USE_REAL_TRANSCRIPTION': 'True', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.transcription_service._call_openai_transcription',
            return_value='Saved real transcript text.',
        ):
            response = self.client.post(reverse('recording-transcribe', args=[recording.id]))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transcript = InterviewTranscript.objects.get(id=response.data['id'])
        self.assertEqual(transcript.recording, recording)
        self.assertEqual(transcript.transcript_text, response.data['transcript_text'])
        self.assertEqual(transcript.transcript_json['algorithm'], 'automatic_speech_recognition')

    def test_real_transcription_disabled_returns_clear_error_without_saving_transcript(self):
        upload_response = self.upload_recording()
        recording = InterviewRecording.objects.get(id=upload_response.data['id'])

        with patch.dict('os.environ', {'USE_REAL_TRANSCRIPTION': 'False', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.transcription_service._call_openai_transcription'
        ) as openai_transcription:
            response = self.client.post(reverse('recording-transcribe', args=[recording.id]))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('Real transcription is disabled', str(response.data['detail']))
        self.assertFalse(InterviewTranscript.objects.filter(recording=recording).exists())
        openai_transcription.assert_not_called()

    def create_transcript(self, text='Candidate communicated clearly and discussed Django API experience.'):
        upload_response = self.upload_recording()
        recording = InterviewRecording.objects.get(id=upload_response.data['id'])
        return InterviewTranscript.objects.create(
            recording=recording,
            transcript_text=text,
            transcript_json={'provider': 'openai', 'mode': 'real'},
        )

    def test_real_summary_requires_explicit_configuration(self):
        transcript = self.create_transcript()

        with patch.dict('os.environ', {'USE_REAL_SUMMARY': 'False'}), patch(
            'apps.ai_services.summary_service._call_openai_summary'
        ) as openai_summary:
            response = self.client.post(reverse('transcript-generate-summary', args=[transcript.id]))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('Real summary generation is disabled', str(response.data['detail']))
        self.assertEqual(InterviewAISummary.objects.filter(transcript=transcript).count(), 0)
        openai_summary.assert_not_called()

    def test_real_summary_missing_api_key_returns_clear_error(self):
        transcript = self.create_transcript()

        with patch.dict('os.environ', {'USE_REAL_SUMMARY': 'True', 'OPENAI_API_KEY': ''}), patch(
            'apps.ai_services.summary_service._call_openai_summary'
        ) as openai_summary:
            response = self.client.post(reverse('transcript-generate-summary', args=[transcript.id]))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('OPENAI_API_KEY is required', str(response.data['detail']))
        self.assertEqual(InterviewAISummary.objects.filter(transcript=transcript).count(), 0)
        openai_summary.assert_not_called()

    def test_real_summary_provider_failure_returns_clear_error(self):
        transcript = self.create_transcript()

        with patch.dict('os.environ', {'USE_REAL_SUMMARY': 'True', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.summary_service._call_openai_summary',
            side_effect=RuntimeError('provider unavailable'),
        ) as openai_summary:
            response = self.client.post(reverse('transcript-generate-summary', args=[transcript.id]))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('Real summary generation failed', str(response.data['detail']))
        self.assertEqual(InterviewAISummary.objects.filter(transcript=transcript).count(), 0)
        openai_summary.assert_called_once()

    def test_real_summary_response_contains_required_structured_output_fields(self):
        transcript = self.create_transcript()

        with patch.dict('os.environ', {'USE_REAL_SUMMARY': 'True', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.summary_service._call_openai_summary',
            return_value=json.dumps({
                'strengths': 'Clear examples.',
                'weaknesses': 'Needs deeper detail.',
                'communication_score': 8,
                'overall_impression': 'Relevant interview performance.',
                'editable_summary_text': 'Clear examples with room for more detail.',
            }),
        ):
            response = self.client.post(reverse('transcript-generate-summary', args=[transcript.id]))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        required_fields = {
            'strengths',
            'weaknesses',
            'communication_score',
            'overall_impression',
            'editable_summary_text',
            'summary_json',
            'transparency',
        }
        self.assertTrue(required_fields.issubset(response.data.keys()))
        self.assertEqual(response.data['transparency']['provider'], 'openai')
        self.assertTrue(response.data['transparency']['human_review_required'])
        self.assertIn('final hiring decision', response.data['transparency']['decision_boundary'])

    def test_interviewer_can_edit_generated_summary_before_final_evaluation(self):
        transcript = self.create_transcript()
        with patch.dict('os.environ', {'USE_REAL_SUMMARY': 'True', 'OPENAI_API_KEY': 'test-key'}), patch(
            'apps.ai_services.summary_service._call_openai_summary',
            return_value=json.dumps({
                'strengths': 'Original strengths.',
                'weaknesses': 'Original weaknesses.',
                'communication_score': 8,
                'overall_impression': 'Original impression.',
                'editable_summary_text': 'Original summary text.',
            }),
        ):
            summary_response = self.client.post(reverse('transcript-generate-summary', args=[transcript.id]))
        summary = InterviewAISummary.objects.get(id=summary_response.data['id'])

        response = self.client.patch(
            reverse('interview-summary-update', args=[summary.id]),
            {
                'strengths': 'Edited strengths after interviewer review.',
                'weaknesses': 'Edited weakness notes.',
                'communication_score': '9.00',
                'overall_impression': 'Edited interviewer impression.',
                'editable_summary_text': 'Edited full summary text.',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        summary.refresh_from_db()
        self.assertEqual(summary.strengths, 'Edited strengths after interviewer review.')
        self.assertEqual(summary.weaknesses, 'Edited weakness notes.')
        self.assertEqual(summary.communication_score, Decimal('9.00'))
        self.assertEqual(summary.overall_impression, 'Edited interviewer impression.')
        self.assertEqual(summary.editable_summary_text, 'Edited full summary text.')
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

from datetime import date, time
from django.utils import timezone
from apps.interviews.models import InterviewerAvailabilityPattern, InterviewerUnavailableDate
from apps.interviews.slot_generation import generate_available_slots


class WeeklyAvailabilitySchedulingTests(InterviewManagementAPITests):
    def create_monday_pattern(self):
        return InterviewerAvailabilityPattern.objects.create(
            organization=self.organization,
            interviewer=self.interviewer,
            day_of_week=InterviewerAvailabilityPattern.DayOfWeek.MONDAY,
            start_time=time(10, 0),
            end_time=time(12, 0),
            slot_duration_minutes=30,
            mode=Interview.Mode.ONLINE,
            meeting_link='https://meet.example.com/weekly',
            effective_from=date(2026, 6, 1),
        )

    def test_monday_weekly_availability_generates_future_monday_slots(self):
        pattern = self.create_monday_pattern()
        now = timezone.make_aware(__import__('datetime').datetime(2026, 6, 24, 8, 0))

        slots = generate_available_slots(self.interviewer, self.organization, days_ahead=14, from_datetime=now)

        monday_slots = [slot for slot in slots if slot.pattern_id == pattern.id]
        self.assertEqual([slot.date for slot in monday_slots[:4]], [date(2026, 6, 29)] * 4)
        self.assertEqual([slot.start_time for slot in monday_slots[:4]], [time(10, 0), time(10, 30), time(11, 0), time(11, 30)])

    def test_booked_and_unavailable_generated_slots_are_excluded(self):
        self.create_monday_pattern()
        InterviewerUnavailableDate.objects.create(organization=self.organization, interviewer=self.interviewer, date=date(2026, 6, 29))
        Interview.objects.create(
            application=self.application,
            organization=self.organization,
            recruiter=self.recruiter,
            interviewer=self.interviewer,
            interview_date=date(2026, 7, 6),
            start_time=time(10, 0),
            end_time=time(10, 30),
            scheduled_datetime=timezone.make_aware(__import__('datetime').datetime(2026, 7, 6, 10, 0)),
            status=Interview.Status.SCHEDULED,
        )
        now = timezone.make_aware(__import__('datetime').datetime(2026, 6, 24, 8, 0))

        slots = generate_available_slots(self.interviewer, self.organization, days_ahead=14, from_datetime=now)

        self.assertNotIn(date(2026, 6, 29), {slot.date for slot in slots})
        self.assertNotIn((date(2026, 7, 6), time(10, 0)), {(slot.date, slot.start_time) for slot in slots})
        self.assertIn((date(2026, 7, 6), time(10, 30)), {(slot.date, slot.start_time) for slot in slots})

    def test_applicant_books_generated_slot_and_second_applicant_cannot_double_book(self):
        pattern = self.create_monday_pattern()
        other_application = JobApplication.objects.create(job=self.job, applicant=self.other_applicant, status=JobApplication.Status.SHORTLISTED)
        first_request = InterviewSchedulingRequest.objects.create(application=self.application, organization=self.organization, recruiter=self.recruiter, interviewer=self.interviewer)
        second_request = InterviewSchedulingRequest.objects.create(application=other_application, organization=self.organization, recruiter=self.recruiter, interviewer=self.interviewer)
        payload = {
            'pattern_id': pattern.id,
            'interview_date': '2026-06-29',
            'start_time': '10:00:00',
            'end_time': '10:30:00',
            'meeting_link': 'https://meet.example.com/weekly',
        }
        with patch('apps.interviews.views.timezone.now', return_value=timezone.make_aware(__import__('datetime').datetime(2026, 6, 24, 8, 0))):
            self.authenticate(self.applicant)
            first_response = self.client.post(reverse('interview-scheduling-request-book', args=[first_request.id]), payload, format='json')
            self.authenticate(self.other_applicant)
            second_response = self.client.post(reverse('interview-scheduling-request-book', args=[second_request.id]), payload, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        interview = Interview.objects.get(application=self.application)
        self.assertEqual(interview.interview_date, date(2026, 6, 29))
        self.assertEqual(interview.start_time, time(10, 0))
        self.assertEqual(interview.end_time, time(10, 30))

    def test_applicant_cannot_book_scheduling_request_they_do_not_own(self):
        pattern = self.create_monday_pattern()
        scheduling_request = InterviewSchedulingRequest.objects.create(application=self.application, organization=self.organization, recruiter=self.recruiter, interviewer=self.interviewer)
        self.authenticate(self.other_applicant)
        response = self.client.post(reverse('interview-scheduling-request-book', args=[scheduling_request.id]), {
            'pattern_id': pattern.id,
            'interview_date': '2026-06-29',
            'start_time': '10:00:00',
            'end_time': '10:30:00',
            'meeting_link': 'https://meet.example.com/weekly',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_interviewer_can_only_manage_own_availability_patterns(self):
        pattern = self.create_monday_pattern()
        self.authenticate(self.other_interviewer)
        response = self.client.delete(reverse('interviewer-availability-pattern-detail', args=[pattern.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_application_available_dates_returns_summary_only(self):
        self.create_monday_pattern()
        InterviewSchedulingRequest.objects.create(application=self.application, organization=self.organization, recruiter=self.recruiter, interviewer=self.interviewer)
        self.authenticate(self.applicant)
        with patch('apps.interviews.slot_generation.timezone.now', return_value=timezone.make_aware(__import__('datetime').datetime(2026, 6, 24, 8, 0))):
            response = self.client.get(reverse('application-interview-available-dates', args=[self.application.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['date'], date(2026, 6, 29))
        self.assertEqual(response.data[0]['day_of_week'], 'Monday')
        self.assertEqual(response.data[0]['available_slot_count'], 4)
        self.assertNotIn('start_time', response.data[0])

    def test_application_available_slots_filters_to_selected_date(self):
        self.create_monday_pattern()
        InterviewSchedulingRequest.objects.create(application=self.application, organization=self.organization, recruiter=self.recruiter, interviewer=self.interviewer)
        self.authenticate(self.applicant)
        with patch('apps.interviews.slot_generation.timezone.now', return_value=timezone.make_aware(__import__('datetime').datetime(2026, 6, 24, 8, 0))):
            response = self.client.get(
                reverse('application-interview-available-slots', args=[self.application.id]),
                {'date': '2026-06-29'},
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        self.assertEqual({slot['date'] for slot in response.data}, {date(2026, 6, 29)})
        self.assertEqual(response.data[0]['start_time'], time(10, 0))
        self.assertEqual(response.data[0]['interviewer_names'], [self.interviewer.full_name])
