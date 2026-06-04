from django.urls import path

from .views import (
    NotificationListAPIView,
    NotificationMarkReadAPIView,
    NotificationReadAllAPIView,
    NotificationUnreadCountAPIView,
)

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='notification-list'),
    path('read-all/', NotificationReadAllAPIView.as_view(), name='notification-read-all'),
    path('unread-count/', NotificationUnreadCountAPIView.as_view(), name='notification-unread-count'),
    path('<int:notification_id>/read/', NotificationMarkReadAPIView.as_view(), name='notification-read'),
]
