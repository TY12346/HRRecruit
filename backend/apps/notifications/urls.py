from django.urls import path

from .views import (
    FirebasePushStatusAPIView,
    NotificationListAPIView,
    NotificationMarkReadAPIView,
    NotificationReadAllAPIView,
    NotificationUnreadCountAPIView,
    PushDeviceDetailAPIView,
    PushDeviceListCreateAPIView,
)

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='notification-list'),
    path('read-all/', NotificationReadAllAPIView.as_view(), name='notification-read-all'),
    path('unread-count/', NotificationUnreadCountAPIView.as_view(), name='notification-unread-count'),
    path('push-status/', FirebasePushStatusAPIView.as_view(), name='notification-push-status'),
    path('push-devices/', PushDeviceListCreateAPIView.as_view(), name='notification-push-device-list'),
    path('push-devices/<int:device_id>/', PushDeviceDetailAPIView.as_view(), name='notification-push-device-detail'),
    path('<int:notification_id>/read/', NotificationMarkReadAPIView.as_view(), name='notification-read'),
]
