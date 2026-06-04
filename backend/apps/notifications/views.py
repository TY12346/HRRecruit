from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


def notifications_for(user):
    return Notification.objects.filter(recipient=user)


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
