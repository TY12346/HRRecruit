from django.contrib import admin

from .models import HiringDecision, JobHiringDecision, JobHiringDecisionItem, JobOffer


class JobHiringDecisionItemInline(admin.TabularInline):
    model = JobHiringDecisionItem
    extra = 0


@admin.register(JobHiringDecision)
class JobHiringDecisionAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_posting', 'decision_type', 'status', 'recruiter', 'submitted_at', 'reviewed_by')
    list_filter = ('decision_type', 'status')
    inlines = [JobHiringDecisionItemInline]


@admin.register(HiringDecision)
class HiringDecisionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'application',
        'recruiter',
        'decision',
        'status',
        'hr_head',
        'submitted_at',
        'reviewed_at',
    )
    list_filter = ('decision', 'status')
    search_fields = (
        'application__job__title',
        'application__applicant__email',
        'recruiter__email',
        'hr_head__email',
        'recruiter_justification',
        'hr_head_justification',
    )


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'offer_status', 'respond_deadline', 'sent_at', 'responded_at')
    list_filter = ('offer_status',)
    search_fields = ('application__job__title', 'application__applicant__email', 'offer_message')
