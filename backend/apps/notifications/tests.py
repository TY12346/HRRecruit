from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.email_service import (
    send_email,
    send_interview_invitation_email,
    send_job_offer_email,
    send_password_reset_otp_email,
    send_subscription_reminder_email,
    send_team_account_created_email,
)
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.users.models import User


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='recipient@example.com',
            password='test-pass-123',
            full_name='Recipient User',
            role=User.Role.APPLICANT,
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='test-pass-123',
            full_name='Other User',
            role=User.Role.APPLICANT,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def test_create_notification_service_stores_related_entity_metadata(self):
        notification = create_notification(
            self.user,
            'application_status_update',
            'Application status updated',
            'Your application status changed.',
            related_entity=self.user,
        )

        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.notification_type, 'application_status_update')
        self.assertEqual(notification.related_entity_type, 'user')
        self.assertEqual(notification.related_entity_id, self.user.id)
        self.assertFalse(notification.is_read)

    def test_user_can_list_and_mark_only_own_notifications_as_read(self):
        own_notification = create_notification(
            self.user,
            'interview_invitation',
            'Interview invitation received',
            'You have a new invitation.',
        )
        other_notification = create_notification(
            self.other_user,
            'interview_invitation',
            'Other invitation',
            'This belongs to another user.',
        )
        self.authenticate(self.user)

        list_response = self.client.get(reverse('notification-list'))
        read_response = self.client.patch(reverse('notification-read', args=[own_notification.id]), {}, format='json')
        forbidden_read_response = self.client.patch(reverse('notification-read', args=[other_notification.id]), {}, format='json')

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in list_response.data], [own_notification.id])
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertTrue(read_response.data['is_read'])
        self.assertEqual(forbidden_read_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unread_count_and_read_all_are_scoped_to_authenticated_user(self):
        create_notification(self.user, 'job_offer_sent', 'Job offer received', 'Offer one.')
        create_notification(self.user, 'job_offer_sent', 'Job offer received', 'Offer two.')
        create_notification(self.other_user, 'job_offer_sent', 'Job offer received', 'Other offer.')
        self.authenticate(self.user)

        count_response = self.client.get(reverse('notification-unread-count'))
        read_all_response = self.client.patch(reverse('notification-read-all'), {}, format='json')
        count_after_response = self.client.get(reverse('notification-unread-count'))

        self.assertEqual(count_response.status_code, status.HTTP_200_OK)
        self.assertEqual(count_response.data['unread_count'], 2)
        self.assertEqual(read_all_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_all_response.data['updated_count'], 2)
        self.assertEqual(count_after_response.data['unread_count'], 0)
        self.assertEqual(Notification.objects.filter(recipient=self.other_user, is_read=False).count(), 1)


class EmailServiceTests(SimpleTestCase):
    @override_settings(
        SENDGRID_API_KEY='SG.test-key',
        SENDGRID_FROM_EMAIL='',
        DEFAULT_FROM_EMAIL='no-reply@hrrecruit.local',
    )
    @patch('apps.notifications.email_service.send_mail')
    def test_send_email_falls_back_to_console_when_sendgrid_from_email_missing(self, mock_send_mail):
        mock_send_mail.return_value = 1

        result = send_email('Subject', 'Message', ['recipient@example.com'])

        self.assertEqual(result['provider'], 'console')
        mock_send_mail.assert_called_once_with(
            subject='Subject',
            message='Message',
            from_email='no-reply@hrrecruit.local',
            recipient_list=['recipient@example.com'],
            fail_silently=False,
        )

    @override_settings(
        SENDGRID_API_KEY='SG.test-key',
        SENDGRID_FROM_EMAIL='sender@example.com',
        DEFAULT_FROM_EMAIL='sender@example.com',
    )
    @patch('apps.notifications.email_service.urlrequest.urlopen')
    def test_send_email_uses_sendgrid_when_configured(self, mock_urlopen):
        mock_response = Mock()
        mock_response.status = 202
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = send_email('Subject', 'Message', ['recipient@example.com'])

        self.assertEqual(result, {'provider': 'sendgrid', 'status_code': 202})
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.sendgrid.com/v3/mail/send')
        self.assertEqual(request.headers['Authorization'], 'Bearer SG.test-key')
        self.assertEqual(request.headers['Content-type'], 'application/json')

    @override_settings(
        SENDGRID_API_KEY='',
        SENDGRID_FROM_EMAIL='',
        DEFAULT_FROM_EMAIL='no-reply@hrrecruit.local',
    )
    @patch('apps.notifications.email_service.send_email')
    def test_email_templates_cover_required_hrrecruit_flows(self, mock_send_email):
        user = SimpleNamespace(
            email='user@example.com',
            full_name='User One',
            role=User.Role.RECRUITER,
            get_role_display=lambda: 'Recruiter',
        )
        job = SimpleNamespace(title='Backend Engineer')
        applicant = SimpleNamespace(email='applicant@example.com', full_name='Applicant One')
        application = SimpleNamespace(applicant=applicant, job=job)
        interview = SimpleNamespace(application=application)
        invitation = SimpleNamespace(
            interview=interview,
            proposed_datetime='2026-06-16 09:00:00+00:00',
            meeting_link='https://meet.example.com/hrrecruit',
            location='',
            get_mode_display=lambda: 'Online',
        )
        offer = SimpleNamespace(
            application=application,
            respond_deadline='2026-06-23 09:00:00+00:00',
            offer_message='We are pleased to offer you the role.',
        )
        subscription = SimpleNamespace(
            organization=SimpleNamespace(name='Example Organization'),
            plan=SimpleNamespace(name='Pro'),
            end_date='2026-06-30',
        )

        send_password_reset_otp_email(user, '123456')
        send_team_account_created_email(user, 'TempPass123!')
        send_interview_invitation_email(invitation)
        send_job_offer_email(offer)
        send_subscription_reminder_email(user, subscription)

        password_reset_call = mock_send_email.call_args_list[0]
        self.assertIn('http://localhost:5173/forgot-password?email=user%40example.com&otp=123456', password_reset_call.kwargs['message'])
        self.assertIn('enter this reset code manually: 123456', password_reset_call.kwargs['message'])

        subjects = [call.kwargs['subject'] for call in mock_send_email.call_args_list]
        self.assertEqual(
            subjects,
            [
                'HRRecruit Password Reset',
                'Your HRRecruit team account',
                'Interview invitation for Backend Engineer',
                'Job offer for Backend Engineer',
                'HRRecruit subscription reminder',
            ],
        )
