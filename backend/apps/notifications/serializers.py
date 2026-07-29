from rest_framework import serializers

from apps.hiring.models import JobOffer
from apps.interviews.models import InterviewSchedulingRequest
from apps.users.models import User
from .models import Notification, PushDevice
from apps.common.serializers import ReadableIdModelSerializer


class NotificationSerializer(ReadableIdModelSerializer):
    title = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

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
            'actions',
        ]
        read_only_fields = fields

    def get_title(self, notification):
        """Enrich legacy generic offer-response titles without rewriting history."""
        if notification.notification_type == 'offer_response' and notification.title in {
            'Job offer accepted', 'Job offer declined', 'Offer accepted', 'Offer declined',
        }:
            offer = self._related_object(notification, JobOffer)
            if offer:
                response = 'accepted' if 'accept' in notification.title.lower() else 'declined'
                return f'{offer.application.applicant.full_name} {response} the job offer for {offer.application.job.title}'
        return notification.title

    def get_actions(self, notification):
        related_type = notification.related_entity_type.lower()
        related_id = notification.related_entity_id
        role = notification.recipient.role

        if related_type == 'joboffer':
            offer = self._related_object(notification, JobOffer)
            if not offer:
                return []
            actions = []
            if role == User.Role.RECRUITER:
                actions.append({'label': 'View offer', 'url': '/recruiter/job-offers'})
                actions.append({'label': 'View job', 'url': f'/recruiter/jobs/{offer.application.job_id}'})
            elif role == User.Role.HR_HEAD:
                actions.append({'label': 'View offer', 'url': '/hiring-manager/job-offers'})
            return actions

        if related_type == 'jobposting' and related_id:
            if role == User.Role.RECRUITER:
                return [{'label': 'View job', 'url': f'/recruiter/jobs/{related_id}'}]
            return []

        if related_type == 'jobapplication' and related_id:
            paths = {
                User.Role.RECRUITER: f'/recruiter/applications/{related_id}',
                User.Role.INTERVIEWER: f'/interviewer/applicants/{related_id}',
                User.Role.HR_HEAD: '/hiring-manager/applicant-search',
            }
            return [{'label': 'View applicant', 'url': paths[role]}] if role in paths else []

        if related_type == 'interview' and related_id:
            paths = {
                User.Role.RECRUITER: '/recruiter/interviews',
                User.Role.INTERVIEWER: f'/interviewer/interviews/{related_id}',
            }
            return [{'label': 'View interview', 'url': paths[role]}] if role in paths else []

        if related_type == 'interviewschedulingrequest':
            scheduling_request = self._related_object(notification, InterviewSchedulingRequest)
            if scheduling_request and role == User.Role.INTERVIEWER:
                return [{'label': 'View interview', 'url': '/interviewer/interviews'}]

        if related_type == 'jobrequisition':
            paths = {
                User.Role.RECRUITER: '/recruiter/job-requisitions',
                User.Role.HR_HEAD: '/hiring-manager/job-requisitions',
            }
            return [{'label': 'View requisition', 'url': paths[role]}] if role in paths else []

        if related_type in {'hiringdecision', 'jobhiringdecision'}:
            paths = {
                User.Role.RECRUITER: '/recruiter/hiring-decisions',
                User.Role.HR_HEAD: '/hiring-manager/hiring-decisions',
            }
            return [{'label': 'View decision', 'url': paths[role]}] if role in paths else []
        return []

    @staticmethod
    def _related_object(notification, model):
        related_entity_id = notification.related_entity_id
        if not related_entity_id:
            return None
        queryset = model.objects
        if model is JobOffer:
            queryset = queryset.select_related('application__applicant', 'application__job')

        # Notification references use the domain object's public ID.  Keep a
        # numeric-PK fallback for notifications created before public IDs were
        # introduced, but never pass a typed ID to an integer database field.
        related_object = queryset.filter(public_id=related_entity_id).first()
        if related_object is None and str(related_entity_id).isdigit():
            return queryset.filter(pk=related_entity_id).first()
        return related_object


class PushDeviceSerializer(ReadableIdModelSerializer):
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
