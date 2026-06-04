from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
