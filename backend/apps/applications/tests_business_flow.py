from decimal import Decimal
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import JobApplication
from apps.billing.models import SubscriptionPlan
from apps.evaluations.models import InterviewRecording
from apps.hiring.models import HiringDecision, JobOffer
from apps.interviews.models import Interview, InterviewInvitation
from apps.jobs.models import EvaluationCriterion, JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


@override_settings(MEDIA_ROOT='/tmp/hrrecruit-test-media')
class HRRecruitBusinessFlowAPITests(TestCase):
    """End-to-end API tests for the current FYP recruitment business flows."""

    password = 'StrongPass123!'

    def setUp(self):
        self.hr_head = User.objects.create_user(
            email='hr-head@example.com',
            password=self.password,
            full_name='HR Head',
            role=User.Role.HR_HEAD,
        )
        self.plan, _ = SubscriptionPlan.objects.update_or_create(
            name=SubscriptionPlan.Name.BASIC,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            defaults={
                'max_job_postings': 1,
                'price': Decimal('99.00'),
                'features_description': 'Basic test plan with one open job.',
                'is_active': True,
            },
        )

    def client_for(self, user=None, email=None, password=None):
        client = APIClient()
        if user or email:
            login_response = client.post(
                reverse('auth-login'),
                {'email': email or user.email, 'password': password or self.password},
                format='json',
            )
            self.assertEqual(login_response.status_code, status.HTTP_200_OK, login_response.data)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['tokens']['access']}")
        return client

    def register_applicant(self, email, full_name):
        client = APIClient()
        register_response = client.post(
            reverse('auth-register'),
            {
                'email': email,
                'full_name': full_name,
                'phone_number': '+60123456789',
                'password': self.password,
            },
            format='json',
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED, register_response.data)
        self.assertEqual(register_response.data['user']['role'], User.Role.APPLICANT)
        self.assertIn('access', register_response.data['tokens'])

        login_response = client.post(
            reverse('auth-login'),
            {'email': email, 'password': self.password},
            format='json',
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, login_response.data)
        self.assertIn('access', login_response.data['tokens'])
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['tokens']['access']}")
        return User.objects.get(email=email), client

    def create_organization_and_team(self):
        hr_client = self.client_for(self.hr_head)
        organization_response = hr_client.post(
            reverse('organization-create'),
            {
                'name': 'Acme Talent Sdn Bhd',
                'registration_no': 'ACME-001',
                'email': 'hr@acme.test',
                'contact_number': '+60312345678',
                'address': 'Kuala Lumpur',
            },
            format='json',
        )
        self.assertEqual(organization_response.status_code, status.HTTP_201_CREATED, organization_response.data)
        organization = Organization.objects.get(id=organization_response.data['organization']['id'])

        subscribe_response = hr_client.post(
            reverse('billing-subscribe'),
            {'plan_id': self.plan.id, 'is_auto_renew': False},
            format='json',
        )
        self.assertEqual(subscribe_response.status_code, status.HTTP_201_CREATED, subscribe_response.data)
        payment_response = hr_client.post(
            reverse('billing-demo-payment-success'),
            {
                'subscription_id': subscribe_response.data['subscription']['id'],
                'transaction_reference': 'DEMO-FLOW-001',
            },
            format='json',
        )
        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED, payment_response.data)

        recruiter_response = hr_client.post(
            reverse('organization-member-list-create'),
            {
                'email': 'recruiter@example.com',
                'full_name': 'Recruiter One',
                'phone_number': '+60111111111',
                'role': User.Role.RECRUITER,
            },
            format='json',
        )
        interviewer_response = hr_client.post(
            reverse('organization-member-list-create'),
            {
                'email': 'interviewer@example.com',
                'full_name': 'Interviewer One',
                'phone_number': '+60222222222',
                'role': User.Role.INTERVIEWER,
            },
            format='json',
        )
        self.assertEqual(recruiter_response.status_code, status.HTTP_201_CREATED, recruiter_response.data)
        self.assertEqual(interviewer_response.status_code, status.HTTP_201_CREATED, interviewer_response.data)

        recruiter = User.objects.get(email='recruiter@example.com')
        interviewer = User.objects.get(email='interviewer@example.com')
        recruiter.set_password(self.password)
        interviewer.set_password(self.password)
        recruiter.save(update_fields=['password'])
        interviewer.save(update_fields=['password'])
        return organization, hr_client, recruiter, self.client_for(recruiter), interviewer, self.client_for(interviewer)

    def create_job_with_evaluation_form(self, recruiter_client):
        job_response = recruiter_client.post(
            reverse('job-list-create'),
            {
                'title': 'Backend Developer',
                'description': 'Build Django APIs with PostgreSQL and React integration.',
                'employment_type': 'Full-time',
                'approximate_salary': '7000.00',
                'location': 'Remote',
                'status': JobPosting.Status.OPEN,
            },
            format='json',
        )
        self.assertEqual(job_response.status_code, status.HTTP_201_CREATED, job_response.data)
        job_id = job_response.data['id']

        form_response = recruiter_client.post(
            reverse('job-evaluation-form', args=[job_id]),
            {
                'title': 'Technical Interview Form',
                'criteria': [
                    {
                        'criterion_name': 'Technical Depth',
                        'description': 'Django and API design depth.',
                        'max_score': '10.00',
                        'weight_score': '1.00',
                    }
                ],
            },
            format='json',
        )
        self.assertEqual(form_response.status_code, status.HTTP_201_CREATED, form_response.data)
        return JobPosting.objects.get(id=job_id), EvaluationCriterion.objects.get(form__job_id=job_id)

    def upload_resume(self, applicant_client):
        response = applicant_client.post(
            reverse('auth-resume-upload'),
            {'resume_file': SimpleUploadedFile('resume.pdf', b'%PDF-1.4 test resume', content_type='application/pdf')},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def apply_for_job(self, applicant_client, job):
        response = applicant_client.post(reverse('job-apply', args=[job.id]), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return JobApplication.objects.get(id=response.data['id'])

    def mock_screening(self, application, changed_by):
        final_score = Decimal('91.00') if application.applicant.email == 'applicant@example.com' else Decimal('70.00')
        application.extracted_resume_text = 'Mock extracted resume text for Django and PostgreSQL.'
        application.extracted_skills = ['django', 'postgresql', 'python']
        application.extracted_experience = {'years': 4}
        application.extracted_education = {'level': 'bachelor'}
        application.semantic_score = Decimal('90.00')
        application.skill_score = Decimal('95.00')
        application.experience_score = Decimal('85.00')
        application.education_score = Decimal('80.00')
        application.final_score = final_score
        application.score_explanation = {'provider': 'mock', 'reason': 'Deterministic test screening.'}
        application.save()
        application.change_status(
            JobApplication.Status.SCREENED_QUALIFIED,
            changed_by=changed_by,
            note='Mock AI-assisted resume screening completed.',
        )
        application.refresh_from_db()
        return application

    @patch('apps.evaluations.views.generate_interview_summary')
    @patch('apps.evaluations.views.transcribe_interview_recording')
    @patch('apps.applications.views.screen_job_application')
    @patch('apps.applications.views.schedule_resume_screening')
    def test_full_recruitment_business_flow_and_subscription_limit(
        self,
        schedule_resume_screening,
        screen_job_application,
        transcribe_interview_recording,
        generate_interview_summary,
    ):
        screen_job_application.side_effect = self.mock_screening
        transcribe_interview_recording.return_value = {
            'transcript_text': 'Mock transcript from interview recording.',
            'transcript_json': {'provider': 'mock-test'},
        }
        generate_interview_summary.return_value = {
            'strengths': 'Strong Django knowledge.',
            'weaknesses': 'Could expand system design examples.',
            'communication_score': Decimal('8.00'),
            'overall_impression': 'Recommended for hire.',
            'editable_summary_text': 'Mock AI summary for test.',
        }

        organization, hr_client, recruiter, recruiter_client, interviewer, interviewer_client = self.create_organization_and_team()
        self.assertTrue(
            OrganizationMembership.objects.filter(
                organization=organization,
                user__in=[self.hr_head, recruiter, interviewer],
                status=OrganizationMembership.Status.ACTIVE,
            ).exists()
        )

        job, criterion = self.create_job_with_evaluation_form(recruiter_client)
        limit_response = recruiter_client.post(
            reverse('job-list-create'),
            {
                'title': 'Second Open Role',
                'description': 'This should exceed the Basic plan open job limit.',
                'employment_type': 'Full-time',
                'approximate_salary': '5000.00',
                'location': 'Remote',
                'status': JobPosting.Status.OPEN,
            },
            format='json',
        )
        self.assertEqual(limit_response.status_code, status.HTTP_400_BAD_REQUEST, limit_response.data)
        self.assertIn('maximum of 1 open job', str(limit_response.data))

        applicant, applicant_client = self.register_applicant('applicant@example.com', 'Applicant One')
        self.upload_resume(applicant_client)
        jobs_response = applicant_client.get(reverse('job-list-create'))
        self.assertEqual(jobs_response.status_code, status.HTTP_200_OK, jobs_response.data)
        self.assertEqual([job_data['id'] for job_data in jobs_response.data], [job.id])

        application = self.apply_for_job(applicant_client, job)
        schedule_resume_screening.assert_called()

        screen_response = recruiter_client.post(reverse('application-screen', args=[application.id]), {}, format='json')
        self.assertEqual(screen_response.status_code, status.HTTP_200_OK, screen_response.data)
        self.assertEqual(screen_response.data['status'], JobApplication.Status.SCREENED_QUALIFIED)
        self.assertEqual(screen_response.data['final_score'], '91.00')

        ranked_response = recruiter_client.get(reverse('job-ranked-candidates', args=[job.id]))
        self.assertEqual(ranked_response.status_code, status.HTTP_200_OK, ranked_response.data)
        self.assertEqual(ranked_response.data[0]['id'], application.id)

        assign_response = recruiter_client.post(
            reverse('application-assign-interviewer', args=[application.id]),
            {'interviewer_id': interviewer.id, 'note': 'Please interview this candidate.'},
            format='json',
        )
        self.assertEqual(assign_response.status_code, status.HTTP_201_CREATED, assign_response.data)
        interview = Interview.objects.get(id=assign_response.data['id'])

        invitation_response = interviewer_client.post(
            reverse('interview-send-invitation', args=[interview.id]),
            {
                'proposed_datetime': (timezone.now() + timezone.timedelta(days=2)).isoformat(),
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/backend-dev',
            },
            format='json',
        )
        self.assertEqual(invitation_response.status_code, status.HTTP_201_CREATED, invitation_response.data)
        invitation = InterviewInvitation.objects.get(id=invitation_response.data['id'])

        accept_response = applicant_client.post(reverse('interview-invitation-accept', args=[invitation.id]), {}, format='json')
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK, accept_response.data)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InterviewInvitation.Status.ACCEPTED)

        recording_response = interviewer_client.post(
            reverse('interview-recording-upload', args=[interview.id]),
            {'audio_file': SimpleUploadedFile('interview.mp3', b'mock audio', content_type='audio/mpeg')},
            format='multipart',
        )
        self.assertEqual(recording_response.status_code, status.HTTP_201_CREATED, recording_response.data)
        recording = InterviewRecording.objects.get(id=recording_response.data['id'])
        transcript_response = interviewer_client.post(reverse('recording-transcribe', args=[recording.id]), {}, format='json')
        self.assertEqual(transcript_response.status_code, status.HTTP_201_CREATED, transcript_response.data)
        summary_response = interviewer_client.post(
            reverse('transcript-generate-summary', args=[transcript_response.data['id']]),
            {},
            format='json',
        )
        self.assertEqual(summary_response.status_code, status.HTTP_201_CREATED, summary_response.data)

        evaluation_response = interviewer_client.post(
            reverse('interview-evaluation-submit', args=[interview.id]),
            {
                'overall_comment': 'Strong candidate for backend role.',
                'answers': [{'criterion_id': criterion.id, 'score': '9.00', 'comment': 'Excellent technical depth.'}],
            },
            format='json',
        )
        self.assertEqual(evaluation_response.status_code, status.HTTP_201_CREATED, evaluation_response.data)

        decision_response = recruiter_client.post(
            reverse('application-hiring-decision', args=[application.id]),
            {'decision': HiringDecision.Decision.HIRE, 'justification': 'Strong evaluation and fit.'},
            format='json',
        )
        self.assertEqual(decision_response.status_code, status.HTTP_201_CREATED, decision_response.data)
        decision = HiringDecision.objects.get(id=decision_response.data['id'])

        pending_response = hr_client.get(reverse('hiring-decision-pending-list'))
        self.assertEqual(pending_response.status_code, status.HTTP_200_OK, pending_response.data)
        self.assertEqual(pending_response.data[0]['id'], decision.id)
        approve_response = hr_client.post(
            reverse('hiring-decision-approve', args=[decision.id]),
            {'justification': 'Approved for offer.'},
            format='json',
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK, approve_response.data)

        offer_response = recruiter_client.post(
            reverse('application-job-offer', args=[application.id]),
            {
                'offer_message': 'We are pleased to offer you the Backend Developer role.',
                'respond_deadline': (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            },
            format='json',
        )
        self.assertEqual(offer_response.status_code, status.HTTP_201_CREATED, offer_response.data)
        offer = JobOffer.objects.get(id=offer_response.data['id'])
        accept_offer_response = applicant_client.post(reverse('job-offer-accept', args=[offer.id]), {}, format='json')
        self.assertEqual(accept_offer_response.status_code, status.HTTP_200_OK, accept_offer_response.data)
        offer.refresh_from_db()
        self.assertEqual(offer.offer_status, JobOffer.OfferStatus.ACCEPTED)

        count_response = applicant_client.get(reverse('notification-unread-count'))
        self.assertEqual(count_response.status_code, status.HTTP_200_OK, count_response.data)
        self.assertGreaterEqual(count_response.data['unread_count'], 1)

        declining_applicant, declining_applicant_client = self.register_applicant(
            'declining-applicant@example.com',
            'Declining Applicant',
        )
        self.upload_resume(declining_applicant_client)
        declining_application = self.apply_for_job(declining_applicant_client, job)
        recruiter_client.post(reverse('application-screen', args=[declining_application.id]), {}, format='json')
        declining_assign_response = recruiter_client.post(
            reverse('application-assign-interviewer', args=[declining_application.id]),
            {'interviewer_id': interviewer.id},
            format='json',
        )
        self.assertIn(declining_assign_response.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED), declining_assign_response.data)
        declining_interview = Interview.objects.get(id=declining_assign_response.data['id'])
        declining_invitation_response = interviewer_client.post(
            reverse('interview-send-invitation', args=[declining_interview.id]),
            {
                'proposed_datetime': (timezone.now() + timezone.timedelta(days=3)).isoformat(),
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/decline',
            },
            format='json',
        )
        self.assertEqual(declining_invitation_response.status_code, status.HTTP_201_CREATED, declining_invitation_response.data)
        decline_invitation_response = declining_applicant_client.post(
            reverse('interview-invitation-decline', args=[declining_invitation_response.data['id']]),
            {'decline_reason': 'Schedule conflict.'},
            format='json',
        )
        self.assertEqual(decline_invitation_response.status_code, status.HTTP_200_OK, decline_invitation_response.data)
        self.assertEqual(decline_invitation_response.data['status'], InterviewInvitation.Status.DECLINED)

        declining_decision_response = recruiter_client.post(
            reverse('application-hiring-decision', args=[declining_application.id]),
            {'decision': HiringDecision.Decision.HIRE, 'justification': 'Proceed after rescheduling offline.'},
            format='json',
        )
        self.assertEqual(declining_decision_response.status_code, status.HTTP_201_CREATED, declining_decision_response.data)
        declining_decision = HiringDecision.objects.get(id=declining_decision_response.data['id'])
        approve_declining_response = hr_client.post(
            reverse('hiring-decision-approve', args=[declining_decision.id]),
            {'justification': 'Approved for alternate offer.'},
            format='json',
        )
        self.assertEqual(approve_declining_response.status_code, status.HTTP_200_OK, approve_declining_response.data)
        decline_offer_create_response = recruiter_client.post(
            reverse('application-job-offer', args=[declining_application.id]),
            {
                'offer_message': 'Alternate offer for declined-interview flow.',
                'respond_deadline': (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            },
            format='json',
        )
        self.assertEqual(decline_offer_create_response.status_code, status.HTTP_201_CREATED, decline_offer_create_response.data)
        decline_offer_response = declining_applicant_client.post(
            reverse('job-offer-decline', args=[decline_offer_create_response.data['id']]),
            {'reason': 'Accepted another role.'},
            format='json',
        )
        self.assertEqual(decline_offer_response.status_code, status.HTTP_200_OK, decline_offer_response.data)
        self.assertEqual(decline_offer_response.data['offer_status'], JobOffer.OfferStatus.DECLINED)

        rejected_applicant, rejected_applicant_client = self.register_applicant('hr-rejected@example.com', 'HR Rejected')
        self.upload_resume(rejected_applicant_client)
        rejected_application = self.apply_for_job(rejected_applicant_client, job)
        rejected_decision_response = recruiter_client.post(
            reverse('application-hiring-decision', args=[rejected_application.id]),
            {'decision': HiringDecision.Decision.HIRE, 'justification': 'Request approval for final check.'},
            format='json',
        )
        self.assertEqual(rejected_decision_response.status_code, status.HTTP_201_CREATED, rejected_decision_response.data)
        reject_response = hr_client.post(
            reverse('hiring-decision-reject', args=[rejected_decision_response.data['id']]),
            {'justification': 'Budget hold.'},
            format='json',
        )
        self.assertEqual(reject_response.status_code, status.HTTP_200_OK, reject_response.data)
        self.assertEqual(reject_response.data['status'], HiringDecision.Status.REJECTED)
