from django.contrib import admin

from .models import ApplicationStageHistory, JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'applicant', 'status', 'final_score', 'applied_at', 'updated_at')
    list_filter = ('status', 'job')
    search_fields = ('job__title', 'applicant__email', 'applicant__full_name', 'recruiter_remark')


@admin.register(ApplicationStageHistory)
class ApplicationStageHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'from_stage', 'to_stage', 'changed_by', 'changed_at')
    list_filter = ('from_stage', 'to_stage')
    search_fields = ('application__job__title', 'application__applicant__email', 'changed_by__email', 'note')
