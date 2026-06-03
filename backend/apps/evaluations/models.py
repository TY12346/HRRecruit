from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.interviews.models import Interview
from apps.jobs.models import EvaluationCriterion
from apps.users.models import User


MAX_INTERVIEW_AUDIO_SIZE_MB = 50
ALLOWED_INTERVIEW_AUDIO_EXTENSIONS = ['mp3', 'wav', 'm4a', 'ogg', 'webm', 'aac']


def validate_interview_audio_size(audio_file):
    max_size = MAX_INTERVIEW_AUDIO_SIZE_MB * 1024 * 1024
    if audio_file.size > max_size:
        raise ValidationError(f'Interview audio file size must not exceed {MAX_INTERVIEW_AUDIO_SIZE_MB} MB.')


class InterviewRecording(models.Model):
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='recordings',
    )
    audio_file = models.FileField(
        upload_to='interview_recordings/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_INTERVIEW_AUDIO_EXTENSIONS),
            validate_interview_audio_size,
        ],
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uploaded_interview_recordings',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Recording for {self.interview}'


class InterviewTranscript(models.Model):
    recording = models.ForeignKey(
        InterviewRecording,
        on_delete=models.CASCADE,
        related_name='transcripts',
    )
    transcript_text = models.TextField()
    transcript_json = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f'Transcript for {self.recording}'


class InterviewAISummary(models.Model):
    transcript = models.ForeignKey(
        InterviewTranscript,
        on_delete=models.CASCADE,
        related_name='ai_summaries',
    )
    strengths = models.TextField()
    weaknesses = models.TextField()
    communication_score = models.DecimalField(max_digits=5, decimal_places=2)
    overall_impression = models.TextField()
    editable_summary_text = models.TextField()
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='edited_interview_ai_summaries',
        blank=True,
        null=True,
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Interview AI summary'
        verbose_name_plural = 'Interview AI summaries'

    def __str__(self):
        return f'AI summary for {self.transcript}'


class InterviewEvaluation(models.Model):
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='evaluations',
    )
    interviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='submitted_interview_evaluations',
        limit_choices_to={'role': User.Role.INTERVIEWER},
    )
    total_score = models.DecimalField(max_digits=5, decimal_places=2)
    overall_comment = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def clean(self):
        super().clean()
        if self.interviewer_id and self.interviewer.role != User.Role.INTERVIEWER:
            raise ValidationError({'interviewer': 'Interview evaluation user must have the interviewer role.'})

    def __str__(self):
        return f'Evaluation for {self.interview} by {self.interviewer.email}'


class EvaluationAnswer(models.Model):
    evaluation = models.ForeignKey(
        InterviewEvaluation,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    criterion = models.ForeignKey(
        EvaluationCriterion,
        on_delete=models.PROTECT,
        related_name='evaluation_answers',
    )
    score = models.DecimalField(max_digits=5, decimal_places=2)
    comment = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['evaluation', 'criterion'],
                name='unique_evaluation_answer_criterion',
            ),
        ]

    def __str__(self):
        return f'{self.criterion} answer for {self.evaluation}'
