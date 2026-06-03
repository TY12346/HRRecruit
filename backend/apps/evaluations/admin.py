from django.contrib import admin

from .models import (
    EvaluationAnswer,
    InterviewAISummary,
    InterviewEvaluation,
    InterviewRecording,
    InterviewTranscript,
)


@admin.register(InterviewRecording)
class InterviewRecordingAdmin(admin.ModelAdmin):
    list_display = ('id', 'interview', 'uploaded_by', 'audio_file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = (
        'interview__application__job__title',
        'interview__application__applicant__email',
        'uploaded_by__email',
        'audio_file',
    )


@admin.register(InterviewTranscript)
class InterviewTranscriptAdmin(admin.ModelAdmin):
    list_display = ('id', 'recording', 'generated_at')
    list_filter = ('generated_at',)
    search_fields = (
        'recording__interview__application__job__title',
        'recording__interview__application__applicant__email',
        'transcript_text',
    )


@admin.register(InterviewAISummary)
class InterviewAISummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'transcript', 'communication_score', 'edited_by', 'generated_at', 'updated_at')
    list_filter = ('generated_at', 'updated_at')
    search_fields = (
        'transcript__recording__interview__application__job__title',
        'transcript__recording__interview__application__applicant__email',
        'strengths',
        'weaknesses',
        'overall_impression',
        'editable_summary_text',
        'edited_by__email',
    )


@admin.register(InterviewEvaluation)
class InterviewEvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'interview', 'interviewer', 'total_score', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = (
        'interview__application__job__title',
        'interview__application__applicant__email',
        'interviewer__email',
        'overall_comment',
    )


@admin.register(EvaluationAnswer)
class EvaluationAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'evaluation', 'criterion', 'score')
    search_fields = (
        'evaluation__interview__application__job__title',
        'evaluation__interview__application__applicant__email',
        'criterion__criterion_name',
        'comment',
    )
