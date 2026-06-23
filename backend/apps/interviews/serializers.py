"""Serializers for interview assignment and self-scheduling APIs."""

from rest_framework import serializers

from apps.applications.serializers import AssignedInterviewerSerializer, JobApplicationSerializer
from apps.users.models import User
from .models import CalendarEvent, Interview, InterviewSchedulingRequest, InterviewStatusHistory, InterviewerAvailabilitySlot


class InterviewStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model = InterviewStatusHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by', 'changed_by_name', 'note', 'changed_at']
        read_only_fields = fields


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = ['id', 'provider', 'external_event_id', 'calendar_link', 'last_synced_at', 'sync_status']
        read_only_fields = fields


class InterviewSerializer(serializers.ModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    interviewer = AssignedInterviewerSerializer(read_only=True)
    calendar_link = serializers.SerializerMethodField()
    status_history = InterviewStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Interview
        fields = [
            'id',
            'application',
            'organization',
            'recruiter',
            'interviewer',
            'scheduled_datetime',
            'availability_slot',
            'scheduling_method',
            'mode',
            'meeting_link',
            'location',
            'status',
            'calendar_link',
            'status_history',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == User.Role.APPLICANT:
            data.pop('recruiter', None)
            data.pop('interviewer', None)
        return data

    def get_calendar_link(self, interview):
        event = interview.calendar_events.order_by('-id').first()
        return event.calendar_link if event else ''


class InterviewerAvailabilitySlotSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)

    class Meta:
        model = InterviewerAvailabilitySlot
        fields = ['id', 'organization', 'interviewer', 'interviewer_name', 'start_datetime', 'end_datetime', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'organization', 'interviewer', 'interviewer_name', 'status', 'created_at', 'updated_at']

    def validate(self, attrs):
        if attrs['end_datetime'] <= attrs['start_datetime']:
            raise serializers.ValidationError({'end_datetime': 'End time must be after start time.'})
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            duplicate_exists = InterviewerAvailabilitySlot.objects.filter(
                interviewer=request.user,
                start_datetime=attrs['start_datetime'],
                end_datetime=attrs['end_datetime'],
            ).exists()
            if duplicate_exists:
                raise serializers.ValidationError({'start_datetime': 'This availability slot already exists.'})
        return attrs


class InterviewSchedulingRequestSerializer(serializers.ModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    interviewer = AssignedInterviewerSerializer(read_only=True)
    selected_slot = InterviewerAvailabilitySlotSerializer(read_only=True)
    available_slots = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSchedulingRequest
        fields = [
            'id', 'application', 'organization', 'recruiter', 'interviewer', 'remark', 'status',
            'expires_at', 'selected_slot', 'interview', 'available_slots', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_available_slots(self, obj):
        if obj.status != InterviewSchedulingRequest.Status.PENDING:
            return []
        slots = InterviewerAvailabilitySlot.objects.filter(
            organization=obj.organization,
            interviewer=obj.interviewer,
            status=InterviewerAvailabilitySlot.Status.AVAILABLE,
        ).order_by('start_datetime')
        return InterviewerAvailabilitySlotSerializer(slots, many=True).data


class CreateSchedulingRequestSerializer(serializers.Serializer):
    interviewer_id = serializers.IntegerField(required=True)
    remark = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class BookSchedulingRequestSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField(required=True)
    mode = serializers.ChoiceField(choices=Interview.Mode.choices, required=False, default=Interview.Mode.ONLINE)
    meeting_link = serializers.URLField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate(self, attrs):
        mode = attrs.get('mode', Interview.Mode.ONLINE)
        if mode == Interview.Mode.ONLINE and not attrs.get('meeting_link', ''):
            raise serializers.ValidationError({'meeting_link': 'Online interviews require a meeting link placeholder.'})
        if mode == Interview.Mode.PHYSICAL and not attrs.get('location', ''):
            raise serializers.ValidationError({'location': 'Physical interviews require a location.'})
        return attrs


class AssignInterviewerSerializer(serializers.Serializer):
    interviewer_id = serializers.IntegerField(required=True)
    note = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
