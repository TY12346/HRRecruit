from django.db import models

from apps.users.models import User


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_entity_type = models.CharField(max_length=100, blank=True)
    related_entity_id = models.PositiveBigIntegerField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['related_entity_type', 'related_entity_id']),
        ]

    def __str__(self):
        return f'{self.recipient.email} - {self.title}'


class PushDevice(models.Model):
    class Platform(models.TextChoices):
        ANDROID = 'android', 'Android'
        IOS = 'ios', 'iOS'
        WEB = 'web', 'Web'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_devices')
    registration_token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    device_id = models.CharField(max_length=255, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active', '-updated_at']),
            models.Index(fields=['platform', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user.email} {self.platform} push device'
