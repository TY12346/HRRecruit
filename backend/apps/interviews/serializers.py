"""Serializers for interview assignment and self-scheduling APIs."""

from django.utils import timezone
from rest_framework import serializers

from apps.applications.serializers import AssignedInterviewerSerializer, JobApplicationSerializer
from apps.users.models import User
from .models import CalendarEvent, Interview, InterviewSchedulingRequest, InterviewStatusHistory, InterviewerAvailabilityPattern, InterviewerUnavailableDate, InterviewerAvailabilitySlot


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
            'interview_date',
            'start_time',
            'end_time',
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


class InterviewerAvailabilityPatternSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = InterviewerAvailabilityPattern
        fields = ['id', 'organization', 'interviewer', 'interviewer_name', 'day_of_week', 'day_name', 'start_time', 'end_time', 'slot_duration_minutes', 'mode', 'meeting_link', 'location', 'effective_from', 'effective_until', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'organization', 'interviewer', 'interviewer_name', 'day_name', 'created_at', 'updated_at']

    def validate(self, attrs):
        if attrs.get('end_time') and attrs.get('start_time') and attrs['end_time'] <= attrs['start_time']:
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})
        if attrs.get('effective_until') and attrs.get('effective_from') and attrs['effective_until'] < attrs['effective_from']:
            raise serializers.ValidationError({'effective_until': 'Effective until cannot be before effective from.'})
        if attrs.get('slot_duration_minutes', 0) < 1:
            raise serializers.ValidationError({'slot_duration_minutes': 'Slot duration must be at least 1 minute.'})
        return attrs


class InterviewerUnavailableDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewerUnavailableDate
        fields = ['id', 'organization', 'interviewer', 'date', 'reason', 'created_at']
        read_only_fields = ['id', 'organization', 'interviewer', 'created_at']


class GeneratedInterviewSlotSerializer(serializers.Serializer):
    id = serializers.CharField()
    pattern_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    start_datetime = serializers.DateTimeField()
    end_datetime = serializers.DateTimeField()
    mode = serializers.CharField()
    meeting_link = serializers.CharField(allow_blank=True)
    location = serializers.CharField(allow_blank=True)
    status = serializers.CharField()


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
        request = self.context.get('request')
        include_slots = request and request.query_params.get('include_available_slots') == '1'
        if obj.status != InterviewSchedulingRequest.Status.PENDING or not include_slots:
            return []
        from .slot_generation import generate_available_slots
        generated_slots = generate_available_slots(obj.interviewer, obj.organization)
        legacy_slots = InterviewerAvailabilitySlot.objects.filter(
            organization=obj.organization,
            interviewer=obj.interviewer,
            status=InterviewerAvailabilitySlot.Status.AVAILABLE,
            start_datetime__gt=timezone.now(),
        ).order_by('start_datetime')
        return GeneratedInterviewSlotSerializer(generated_slots, many=True).data + InterviewerAvailabilitySlotSerializer(legacy_slots, many=True).data


class CreateSchedulingRequestSerializer(serializers.Serializer):
    interviewer_id = serializers.IntegerField(required=True)
    remark = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class BookSchedulingRequestSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField(required=False)
    pattern_id = serializers.IntegerField(required=False)
    interview_date = serializers.DateField(required=False)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    mode = serializers.ChoiceField(choices=Interview.Mode.choices, required=False, default=Interview.Mode.ONLINE)
    meeting_link = serializers.URLField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate(self, attrs):
        if not attrs.get('slot_id') and not all(attrs.get(field) for field in ['pattern_id', 'interview_date', 'start_time', 'end_time']):
            raise serializers.ValidationError({'slot_id': 'Provide either a legacy slot_id or generated slot pattern/date/time fields.'})
        mode = attrs.get('mode', Interview.Mode.ONLINE)
        if mode == Interview.Mode.ONLINE and not attrs.get('meeting_link', ''):
            raise serializers.ValidationError({'meeting_link': 'Online interviews require a meeting link placeholder.'})
        if mode == Interview.Mode.PHYSICAL and not attrs.get('location', ''):
            raise serializers.ValidationError({'location': 'Physical interviews require a location.'})
        return attrs


class AssignInterviewerSerializer(serializers.Serializer):
    interviewer_id = serializers.IntegerField(required=True)
    note = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
