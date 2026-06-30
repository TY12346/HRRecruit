from .models import Notification
from .push_service import FirebasePushUnavailable, send_notification_push


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
    _deliver_push_safely(notification)
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
        _deliver_push_safely(notification)
    return created_notifications


def _deliver_push_safely(notification):
    """Attempt Firebase push without breaking the database notification workflow."""
    try:
        return send_notification_push(notification)
    except FirebasePushUnavailable as exc:
        return {'provider': 'firebase_fcm', 'status': 'unavailable', 'error': str(exc)}
    except Exception as exc:
        return {'provider': 'firebase_fcm', 'status': 'failed', 'error': exc.__class__.__name__}
