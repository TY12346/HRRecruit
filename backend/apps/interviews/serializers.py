"""Serializers for interview assignment and self-scheduling APIs."""

from django.utils import timezone
from rest_framework import serializers

from apps.applications.serializers import AssignedInterviewerSerializer, JobApplicationSerializer
from apps.jobs.serializers import EvaluationCriterionSerializer
from apps.users.models import User
from .models import CalendarEvent, Interview, InterviewSchedulingRequest, InterviewStatusHistory, InterviewerAvailabilityPattern, InterviewerUnavailableDate, InterviewerAvailabilitySlot
from .slot_generation import generate_common_available_slots
from apps.common.serializers import ReadableIdModelSerializer


class GoogleCalendarOAuthCallbackSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, trim_whitespace=True)
    state = serializers.CharField(required=True, trim_whitespace=True)


class GoogleCalendarConnectSerializer(serializers.Serializer):
    next = serializers.URLField(required=False, allow_blank=True)


class InterviewStatusHistorySerializer(ReadableIdModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model = InterviewStatusHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by', 'changed_by_name', 'note', 'changed_at']
        read_only_fields = fields


class CalendarEventSerializer(ReadableIdModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = ['id', 'provider', 'external_event_id', 'calendar_link', 'last_synced_at', 'sync_status']
        read_only_fields = fields


class InterviewSerializer(ReadableIdModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    interviewer = AssignedInterviewerSerializer(read_only=True)
    panel_interviewers = AssignedInterviewerSerializer(many=True, read_only=True)
    calendar_link = serializers.SerializerMethodField()
    evaluation_criteria = serializers.SerializerMethodField()
    status_history = InterviewStatusHistorySerializer(many=True, read_only=True)
    latest_recording = serializers.SerializerMethodField()
    transcript = serializers.SerializerMethodField()
    ai_summary = serializers.SerializerMethodField()
    deliverable_status = serializers.SerializerMethodField()
    evaluation_submitted = serializers.SerializerMethodField()
    has_common_availability = serializers.SerializerMethodField()
    availability_alert = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            'id',
            'application',
            'organization',
            'recruiter',
            'interviewer',
            'panel_interviewers',
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
            'evaluation_criteria',
            'status_history',
            'latest_recording',
            'transcript',
            'ai_summary',
            'deliverable_status',
            'evaluation_submitted',
            'has_common_availability',
            'availability_alert',
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
            data.pop('panel_interviewers', None)
        return data

    def get_calendar_link(self, interview):
        event = interview.calendar_events.order_by('-id').first()
        return event.calendar_link if event else ''

    def get_latest_recording(self, interview):
        from apps.evaluations.models import InterviewRecording
        from apps.evaluations.serializers import InterviewRecordingSerializer

        recording = InterviewRecording.objects.filter(interview=interview).order_by('-uploaded_at').first()
        return InterviewRecordingSerializer(recording, context=self.context).data if recording else None

    def get_transcript(self, interview):
        from apps.evaluations.models import InterviewTranscript
        from apps.evaluations.serializers import InterviewTranscriptSerializer

        transcript = InterviewTranscript.objects.filter(recording__interview=interview).order_by('-generated_at').first()
        return InterviewTranscriptSerializer(transcript, context=self.context).data if transcript else None

    def get_ai_summary(self, interview):
        from apps.evaluations.models import InterviewAISummary
        from apps.evaluations.serializers import InterviewAISummarySerializer

        summary = InterviewAISummary.objects.filter(transcript__recording__interview=interview).order_by('-updated_at').first()
        return InterviewAISummarySerializer(summary, context=self.context).data if summary else None

    def get_deliverable_status(self, interview):
        from apps.evaluations.deliverables import deliverable_status_for

        status = deliverable_status_for(interview)
        return {
            **status,
            'deadline': status['deadline'].isoformat() if status['deadline'] else None,
        }

    def get_evaluation_criteria(self, interview):
        form = getattr(interview.application.job, 'interview_evaluation_form', None)
        if not form:
            return []
        return EvaluationCriterionSerializer(form.criteria.all(), many=True).data

    def get_evaluation_submitted(self, interview):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == User.Role.INTERVIEWER:
            return interview.evaluations.filter(interviewer=request.user).exists()
        return interview.evaluations.exists()

    def get_has_common_availability(self, interview):
        if interview.status != Interview.Status.INVITED:
            return True
        panel = list(interview.panel_interviewers.all()) or ([interview.interviewer] if interview.interviewer else [])
        return bool(generate_common_available_slots(panel, interview.organization))

    def get_availability_alert(self, interview):
        if self.get_has_common_availability(interview):
            return ''
        return 'No common availability timeslot exists for all assigned interviewers. The applicant has not been invited.'


class InterviewerAvailabilityPatternSerializer(ReadableIdModelSerializer):
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


class InterviewerUnavailableDateSerializer(ReadableIdModelSerializer):
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


class InterviewerAvailabilitySlotSerializer(ReadableIdModelSerializer):
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


class InterviewSchedulingRequestSerializer(ReadableIdModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    interviewer = AssignedInterviewerSerializer(read_only=True)
    panel_interviewers = AssignedInterviewerSerializer(many=True, read_only=True)
    selected_slot = InterviewerAvailabilitySlotSerializer(read_only=True)
    available_slots = serializers.SerializerMethodField()
    has_common_availability = serializers.SerializerMethodField()
    availability_alert = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSchedulingRequest
        fields = [
            'id', 'application', 'organization', 'recruiter', 'interviewer', 'panel_interviewers', 'remark', 'status',
            'expires_at', 'selected_slot', 'interview', 'available_slots', 'has_common_availability',
            'availability_alert', 'invitation_sent_at', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_available_slots(self, obj):
        request = self.context.get('request')
        include_slots = request and request.query_params.get('include_available_slots') == '1'
        if obj.status != InterviewSchedulingRequest.Status.PENDING or not include_slots:
            return []
        panel = list(obj.panel_interviewers.all()) or [obj.interviewer]
        generated_slots = generate_common_available_slots(panel, obj.organization)
        legacy_slots = []
        if len(panel) == 1:
            legacy_slots = InterviewerAvailabilitySlot.objects.filter(
                organization=obj.organization,
                interviewer=obj.interviewer,
                status=InterviewerAvailabilitySlot.Status.AVAILABLE,
                start_datetime__gt=timezone.now(),
            ).order_by('start_datetime')
        return GeneratedInterviewSlotSerializer(generated_slots, many=True).data + InterviewerAvailabilitySlotSerializer(legacy_slots, many=True).data

    def get_has_common_availability(self, obj):
        if obj.status != InterviewSchedulingRequest.Status.PENDING:
            return True
        panel = list(obj.panel_interviewers.all()) or [obj.interviewer]
        if generate_common_available_slots(panel, obj.organization):
            return True
        return len(panel) == 1 and InterviewerAvailabilitySlot.objects.filter(
            organization=obj.organization,
            interviewer=obj.interviewer,
            status=InterviewerAvailabilitySlot.Status.AVAILABLE,
            start_datetime__gt=timezone.now(),
        ).exists()

    def get_availability_alert(self, obj):
        if self.get_has_common_availability(obj):
            return ''
        return 'No common availability timeslot exists for all assigned interviewers. The applicant has not been invited.'


class CreateSchedulingRequestSerializer(serializers.Serializer):
    interviewer_id = serializers.IntegerField(required=False)
    interviewer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False,
    )
    remark = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        interviewer_ids = attrs.get('interviewer_ids') or []
        if attrs.get('interviewer_id'):
            interviewer_ids = [attrs['interviewer_id'], *interviewer_ids]
        interviewer_ids = list(dict.fromkeys(interviewer_ids))
        if not interviewer_ids:
            raise serializers.ValidationError({'interviewer_ids': 'Select at least one interviewer for the panel.'})
        attrs['interviewer_ids'] = interviewer_ids
        attrs['interviewer_id'] = interviewer_ids[0]
        return attrs


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
        return attrs


class AssignInterviewerSerializer(serializers.Serializer):
    interviewer_id = serializers.IntegerField(required=False)
    interviewer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False,
        max_length=3,
    )
    note = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate(self, attrs):
        interviewer_ids = attrs.get('interviewer_ids')
        interviewer_id = attrs.get('interviewer_id')
        if interviewer_ids is None and interviewer_id is None:
            raise serializers.ValidationError({'interviewer_ids': 'Select at least one interviewer.'})
        if interviewer_ids is not None and len(set(interviewer_ids)) != len(interviewer_ids):
            raise serializers.ValidationError({'interviewer_ids': 'Each interviewer may only be selected once.'})
        attrs['interviewer_ids'] = interviewer_ids if interviewer_ids is not None else [interviewer_id]
        return attrs
