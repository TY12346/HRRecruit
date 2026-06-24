from django.contrib import admin

from .models import CalendarEvent, Interview, InterviewSchedulingRequest, InterviewStatusHistory, InterviewerAvailabilitySlot


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'application',
        'organization',
        'recruiter',
        'interviewer',
        'scheduled_datetime',
        'mode',
        'status',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'mode', 'organization')
    search_fields = (
        'application__job__title',
        'application__applicant__email',
        'recruiter__email',
        'interviewer__email',
        'meeting_link',
        'location',
    )


@admin.register(InterviewStatusHistory)
class InterviewStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'interview', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('from_status', 'to_status')
    search_fields = ('interview__application__job__title', 'interview__application__applicant__email', 'changed_by__email', 'note')


@admin.register(InterviewerAvailabilitySlot)
class InterviewerAvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'interviewer', 'start_datetime', 'end_datetime', 'status')
    list_filter = ('status', 'organization')
    search_fields = ('interviewer__email', 'interviewer__full_name')


@admin.register(InterviewSchedulingRequest)
class InterviewSchedulingRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'organization', 'recruiter', 'interviewer', 'status', 'expires_at')
    list_filter = ('status', 'organization')
    search_fields = ('application__job__title', 'application__applicant__email', 'recruiter__email', 'interviewer__email', 'remark')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'interview', 'provider', 'sync_status', 'external_event_id', 'last_synced_at')
    list_filter = ('provider', 'sync_status')
    search_fields = ('interview__application__job__title', 'interview__application__applicant__email', 'external_event_id', 'calendar_link')
