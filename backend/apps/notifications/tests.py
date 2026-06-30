from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.email_service import (
    build_password_reset_link,
    send_email,
    send_job_offer_email,
    send_password_reset_otp_email,
    send_subscription_reminder_email,
    send_team_account_created_email,
)
from apps.notifications.models import Notification, PushDevice
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
            'interview_scheduled',
            'Interview scheduled',
            'You have a scheduled interview.',
        )
        other_notification = create_notification(
            self.other_user,
            'interview_scheduled',
            'Other interview update',
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

    def test_user_can_register_list_and_deactivate_push_device(self):
        self.authenticate(self.user)
        payload = {
            'registration_token': 'fcm-token-' + ('x' * 32),
            'platform': 'android',
            'device_id': 'pixel-demo-device',
            'app_version': '0.1.0',
        }

        create_response = self.client.post(reverse('notification-push-device-list'), payload, format='json')
        list_response = self.client.get(reverse('notification-push-device-list'))

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data['platform'], 'android')
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]['device_id'], 'pixel-demo-device')

        delete_response = self.client.delete(reverse('notification-push-device-detail', args=[create_response.data['id']]))
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PushDevice.objects.get(id=create_response.data['id']).is_active)

    def test_push_device_registration_is_scoped_to_authenticated_user(self):
        other_device = PushDevice.objects.create(
            user=self.other_user,
            registration_token='fcm-token-' + ('y' * 32),
            platform=PushDevice.Platform.ANDROID,
        )
        self.authenticate(self.user)

        response = self.client.delete(reverse('notification-push-device-detail', args=[other_device.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        other_device.refresh_from_db()
        self.assertTrue(other_device.is_active)

    def test_firebase_push_status_endpoint_reports_configuration(self):
        self.authenticate(self.user)

        response = self.client.get(reverse('notification-push-status'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('enabled', response.data)
        self.assertIn('ready', response.data)

    @override_settings(FIREBASE_PUSH_ENABLED=True)
    @patch('apps.notifications.push_service._firebase_app')
    @patch('apps.notifications.push_service._firebase_messaging_module')
    def test_firebase_push_service_sends_to_registered_device(self, mock_messaging_module, _mock_firebase_app):
        from apps.notifications.push_service import send_notification_push

        class FakeResponseItem:
            success = True

        class FakeBatchResponse:
            success_count = 1
            failure_count = 0
            responses = [FakeResponseItem()]

        fake_messaging = Mock()
        fake_messaging.Notification.side_effect = lambda title, body: {'title': title, 'body': body}
        fake_messaging.MulticastMessage.side_effect = lambda notification, tokens, data: {
            'notification': notification,
            'tokens': tokens,
            'data': data,
        }
        fake_messaging.send_each_for_multicast.return_value = FakeBatchResponse()
        mock_messaging_module.return_value = fake_messaging
        PushDevice.objects.create(
            user=self.user,
            registration_token='fcm-token-' + ('z' * 32),
            platform=PushDevice.Platform.ANDROID,
        )
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='interview_scheduled',
            title='Interview scheduled',
            message='Your interview is scheduled.',
        )

        result = send_notification_push(notification)

        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['success_count'], 1)
        fake_messaging.send_each_for_multicast.assert_called_once()


class EmailServiceTests(SimpleTestCase):
    @override_settings(
        SENDGRID_API_KEY='SG.test-key',
        SENDGRID_FROM_EMAIL='',
        DEFAULT_FROM_EMAIL='no-reply@hrrecruit.local',
    )
    @patch('apps.notifications.email_service.send_mail')
    def test_send_email_falls_back_to_django_backend_when_sendgrid_from_email_missing(self, mock_send_mail):
        mock_send_mail.return_value = 1

        result = send_email('Subject', 'Message', ['recipient@example.com'])

        self.assertEqual(result['provider'], 'locmem')
        mock_send_mail.assert_called_once_with(
            subject='Subject',
            message='Message',
            from_email='no-reply@hrrecruit.local',
            recipient_list=['recipient@example.com'],
            fail_silently=False,
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        SENDGRID_API_KEY='',
        SENDGRID_FROM_EMAIL='',
        DEFAULT_FROM_EMAIL='sender@example.com',
    )
    @patch('apps.notifications.email_service.send_mail')
    def test_send_email_reports_smtp_provider_when_smtp_backend_is_configured(self, mock_send_mail):
        mock_send_mail.return_value = 1

        result = send_email('Subject', 'Message', ['recipient@example.com'])

        self.assertEqual(result['provider'], 'smtp')
        self.assertEqual(result['sent_count'], 1)

    @override_settings(FRONTEND_PASSWORD_RESET_URL='http://localhost:5173/forgot-password')
    def test_web_password_reset_link_uses_reset_password_page_even_with_old_env_value(self):
        user = SimpleNamespace(email='user@example.com')

        reset_link = build_password_reset_link(user, '123456', client_app='web')

        self.assertEqual(
            reset_link,
            'http://localhost:5173/reset-password?email=user%40example.com&token=123456',
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


    @patch('apps.notifications.email_service.send_email')
    def test_mobile_password_reset_email_contains_otp_without_link(self, mock_send_email):
        user = SimpleNamespace(email='applicant@example.com', full_name='Applicant One')

        send_password_reset_otp_email(user, '654321', client_app='mobile')

        password_reset_call = mock_send_email.call_args
        self.assertIn('Use the OTP below', password_reset_call.kwargs['message'])
        self.assertIn('654321', password_reset_call.kwargs['message'])
        self.assertNotIn('http://', password_reset_call.kwargs['message'])
        self.assertNotIn('https://', password_reset_call.kwargs['message'])

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

        send_password_reset_otp_email(user, '123456', client_app='web')
        send_team_account_created_email(user, 'TempPass123!')
        send_job_offer_email(offer)
        send_subscription_reminder_email(user, subscription)

        password_reset_call = mock_send_email.call_args_list[0]
        self.assertIn('http://localhost:5173/reset-password?email=user%40example.com&token=123456', password_reset_call.kwargs['message'])
        self.assertNotIn('enter this reset code manually', password_reset_call.kwargs['message'])

        subjects = [call.kwargs['subject'] for call in mock_send_email.call_args_list]
        self.assertEqual(
            subjects,
            [
                'HRRecruit Password Reset',
                'Your HRRecruit team account',
                'Job offer for Backend Engineer',
                'HRRecruit subscription reminder',
            ],
        )
