from .models import Notification


def create_in_app_notification(user, title, message, data=None):
    return Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        data=data or {},
    )


def create_bulk_in_app_notifications(users, title, message, data=None):
    return [create_in_app_notification(user, title, message, data) for user in users]
