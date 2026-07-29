"""Interview deliverable deadline helpers and notifications."""

from datetime import timedelta

from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from .models import InterviewAISummary, InterviewEvaluation, InterviewRecording, InterviewTranscript, ProcessingStatus

DELIVERABLE_DEADLINE_DAYS = 3
ALMOST_LATE_WINDOW = timedelta(hours=24)
ALMOST_LATE_NOTIFICATION_TYPE = 'interview_deliverables_almost_late'
LATE_NOTIFICATION_TYPE = 'interview_deliverables_late'


def deliverable_deadline_for(interview):
    if not interview.scheduled_datetime:
        return None
    return interview.scheduled_datetime + timedelta(days=DELIVERABLE_DEADLINE_DAYS)


def latest_transcript_for(interview):
    return InterviewTranscript.objects.filter(
        recording__interview=interview,
        processing_status__in=[ProcessingStatus.COMPLETED, ProcessingStatus.LOW_QUALITY],
    ).exclude(transcript_text='').order_by('-generated_at').first()


def latest_ai_summary_for(interview):
    return InterviewAISummary.objects.filter(transcript__recording__interview=interview).order_by('-updated_at').first()


def evaluation_for(interview):
    return InterviewEvaluation.objects.filter(interview=interview).order_by('-submitted_at').first()


def assigned_interviewer_ids(interview):
    interviewer_ids = set(interview.panel_interviewers.values_list('id', flat=True))
    if interview.interviewer_id:
        interviewer_ids.add(interview.interviewer_id)
    return interviewer_ids


def deliverable_status_for(interview, at_time=None):
    at_time = at_time or timezone.now()
    deadline = deliverable_deadline_for(interview)
    recording = InterviewRecording.objects.filter(interview=interview).order_by('-uploaded_at').first()
    transcript = latest_transcript_for(interview)
    summary = latest_ai_summary_for(interview)
    evaluation = evaluation_for(interview)
    submitted_interviewer_ids = set(
        InterviewEvaluation.objects.filter(interview=interview).values_list('interviewer_id', flat=True)
    )
    expected_interviewer_ids = assigned_interviewer_ids(interview)
    missing = []
    if not recording or not recording.audio_file:
        missing.append('audio_recording')
    if not transcript:
        missing.append('transcript')
    if not summary:
        missing.append('ai_summary')
    if not expected_interviewer_ids or not expected_interviewer_ids.issubset(submitted_interviewer_ids):
        missing.append('evaluation_scorecard')
    is_complete = not missing
    is_late = bool(deadline and at_time > deadline and not is_complete)
    is_almost_late = bool(deadline and not is_complete and not is_late and deadline - ALMOST_LATE_WINDOW <= at_time <= deadline)
    return {
        'deadline': deadline,
        'missing': missing,
        'is_complete': is_complete,
        'is_almost_late': is_almost_late,
        'is_late': is_late,
        'transcript_id': transcript.public_id if transcript else None,
        'ai_summary_id': summary.public_id if summary else None,
        'evaluation_id': evaluation.public_id if evaluation else None,
        'submitted_evaluation_count': len(expected_interviewer_ids & submitted_interviewer_ids),
        'required_evaluation_count': len(expected_interviewer_ids),
    }


def create_interviewer_deadline_notification(interview, notification_type, title, message):
    if not interview.interviewer_id:
        return None
    exists = Notification.objects.filter(
        recipient=interview.interviewer,
        notification_type=notification_type,
        related_entity_type='interview',
        related_entity_id=interview.public_id,
    ).exists()
    if exists:
        return None
    return create_notification(interview.interviewer, notification_type, title, message, related_entity=interview)
