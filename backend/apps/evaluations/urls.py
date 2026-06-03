"""URL routes for interview recording, transcript, and summary APIs."""

from django.urls import path

from .views import (
    InterviewAISummaryUpdateAPIView,
    InterviewRecordingTranscribeAPIView,
    InterviewTranscriptGenerateSummaryAPIView,
)

urlpatterns = [
    path('recordings/<int:recording_id>/transcribe/', InterviewRecordingTranscribeAPIView.as_view(), name='recording-transcribe'),
    path('transcripts/<int:transcript_id>/generate-summary/', InterviewTranscriptGenerateSummaryAPIView.as_view(), name='transcript-generate-summary'),
    path('interview-summaries/<int:summary_id>/', InterviewAISummaryUpdateAPIView.as_view(), name='interview-summary-update'),
]
