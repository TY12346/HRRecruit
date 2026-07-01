from .models import Notification
from .push_service import (
    FCM_PUSH_CHANNEL,
    FIREBASE_ADMIN_SDK,
    FIREBASE_FCM_PROVIDER,
    FirebasePushUnavailable,
    send_fcm_notification_push,
)


def _related_entity_values(related_entity):
    if related_entity is None:
        return '', None
    return related_entity._meta.model_name, related_entity.pk


def create_notification(recipient, notification_type, title, message, related_entity=None):
    related_entity_type, related_entity_id = _related_entity_values(related_entity)
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    _deliver_fcm_push_safely(notification)
    return notification


def create_bulk_notifications(recipients, notification_type, title, message, related_entity=None):
    related_entity_type, related_entity_id = _related_entity_values(related_entity)
    notifications = [
        Notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        for recipient in recipients
    ]
    created_notifications = Notification.objects.bulk_create(notifications)
    for notification in created_notifications:
        _deliver_fcm_push_safely(notification)
    return created_notifications


def _deliver_fcm_push_safely(notification):
    """Attempt FCM push delivery without breaking database notifications."""
    try:
        return send_fcm_notification_push(notification)
    except FirebasePushUnavailable as exc:
        return _fcm_delivery_error('unavailable', str(exc))
    except Exception as exc:
        return _fcm_delivery_error('failed', exc.__class__.__name__)


def _fcm_delivery_error(status, error):
    return {
        'channel': FCM_PUSH_CHANNEL,
        'provider': FIREBASE_FCM_PROVIDER,
        'sdk': FIREBASE_ADMIN_SDK,
        'status': status,
        'error': error,
    }
