from django.contrib import admin

from .models import EvaluationCriterion, InterviewEvaluationForm, JobPosting, JobRequirement, SavedJobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organization', 'recruiter', 'employment_type', 'location', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'employment_type', 'organization')
    search_fields = ('title', 'description', 'location', 'organization__name', 'recruiter__email')


@admin.register(JobRequirement)
class JobRequirementAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'requirement_type', 'weight_score', 'minimum_threshold', 'created_at')
    list_filter = ('requirement_type',)
    search_fields = ('job__title', 'description')


@admin.register(InterviewEvaluationForm)
class InterviewEvaluationFormAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'job', 'created_at')
    search_fields = ('title', 'job__title')


@admin.register(EvaluationCriterion)
class EvaluationCriterionAdmin(admin.ModelAdmin):
    list_display = ('id', 'criterion_name', 'form', 'max_score', 'weight_score', 'created_at')
    search_fields = ('criterion_name', 'description', 'form__title', 'form__job__title')


@admin.register(SavedJobPosting)
class SavedJobPostingAdmin(admin.ModelAdmin):
    list_display = ('id', 'applicant', 'job', 'saved_at')
    search_fields = ('applicant__email', 'applicant__full_name', 'job__title')
