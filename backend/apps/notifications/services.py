from .models import Notification


def _related_entity_values(related_entity):
    if related_entity is None:
        return '', None
    return related_entity._meta.model_name, related_entity.pk


def create_notification(recipient, notification_type, title, message, related_entity=None):
    related_entity_type, related_entity_id = _related_entity_values(related_entity)
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )


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
    return Notification.objects.bulk_create(notifications)
