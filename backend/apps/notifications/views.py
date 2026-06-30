from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, PushDevice
from .push_service import firebase_push_status
from .serializers import NotificationSerializer, PushDeviceSerializer


def notifications_for(user):
    return Notification.objects.filter(recipient=user)


def push_devices_for(user):
    return PushDevice.objects.filter(user=user)


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = notifications_for(request.user)
        return Response(NotificationSerializer(notifications, many=True).data)


class NotificationMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        notification = get_object_or_404(notifications_for(request.user), id=notification_id)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        updated_count = notifications_for(request.user).filter(is_read=False).update(is_read=True)
        return Response({'updated_count': updated_count})


class NotificationUnreadCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'unread_count': notifications_for(request.user).filter(is_read=False).count()})


class PushDeviceListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = push_devices_for(request.user)
        return Response(PushDeviceSerializer(devices, many=True).data)

    def post(self, request):
        serializer = PushDeviceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        return Response(PushDeviceSerializer(device).data, status=status.HTTP_201_CREATED)


class PushDeviceDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, device_id):
        device = get_object_or_404(push_devices_for(request.user), id=device_id)
        device.is_active = False
        device.save(update_fields=['is_active', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class FirebasePushStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(firebase_push_status())
