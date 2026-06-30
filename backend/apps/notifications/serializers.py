from rest_framework import serializers

from .models import Notification, PushDevice


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'related_entity_type',
            'related_entity_id',
            'is_read',
            'created_at',
        ]
        read_only_fields = fields


class PushDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushDevice
        fields = [
            'id',
            'registration_token',
            'platform',
            'device_id',
            'app_version',
            'is_active',
            'created_at',
            'updated_at',
            'last_seen_at',
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at', 'last_seen_at']

    def validate_registration_token(self, value):
        value = str(value or '').strip()
        if len(value) < 20:
            raise serializers.ValidationError('Enter a valid FCM registration token.')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        token = validated_data.pop('registration_token')
        device, _created = PushDevice.objects.update_or_create(
            registration_token=token,
            defaults={
                **validated_data,
                'user': user,
                'is_active': True,
            },
        )
        return device
