"""In-process background jobs for real transcription (no fake output)."""
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from django.db import close_old_connections
from django.utils import timezone
from apps.ai_services.transcription_service import TranscriptionUnavailable, transcribe_recording_payload
from .models import InterviewTranscript, ProcessingStatus

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='real-transcription')

STALE_TRANSCRIPTION_ERROR = (
    'Transcription stopped before it completed. The backend may have restarted or the '
    'processing time limit was exceeded. Please regenerate the transcript.'
)


def _stale_after():
    """Return the maximum time a non-durable in-process job may remain active."""
    try:
        minutes = max(1, int(os.getenv('TRANSCRIPTION_STALE_MINUTES', '30')))
    except ValueError:
        minutes = 30
    return timedelta(minutes=minutes)


def expire_stale_transcription(transcript, *, now=None):
    """Turn an orphaned pending/processing row into an actionable failure.

    Thread-pool work is lost when the web process restarts. Without this guard those
    rows remain in PROCESSING forever and clients continue polling indefinitely.
    """
    if transcript.processing_status not in (ProcessingStatus.PENDING, ProcessingStatus.PROCESSING):
        return transcript
    if (now or timezone.now()) - transcript.generated_at <= _stale_after():
        return transcript

    changed = InterviewTranscript.objects.filter(
        pk=transcript.pk,
        processing_status__in=(ProcessingStatus.PENDING, ProcessingStatus.PROCESSING),
    ).update(
        processing_status=ProcessingStatus.FAILED,
        processing_error=STALE_TRANSCRIPTION_ERROR,
        transcript_json={
            'error': STALE_TRANSCRIPTION_ERROR,
            'failed_at': (now or timezone.now()).isoformat(),
            'failure_reason': 'stale_background_job',
        },
    )
    if changed:
        transcript.processing_status = ProcessingStatus.FAILED
        transcript.processing_error = STALE_TRANSCRIPTION_ERROR
        transcript.transcript_json = {
            'error': STALE_TRANSCRIPTION_ERROR,
            'failed_at': (now or timezone.now()).isoformat(),
            'failure_reason': 'stale_background_job',
        }
    return transcript

def enqueue_transcription(transcript_id):
    _executor.submit(_process, transcript_id)

def _process(transcript_id):
    close_old_connections()
    try:
        transcript = InterviewTranscript.objects.select_related('recording').get(pk=transcript_id)
        transcript.processing_status = ProcessingStatus.PROCESSING
        transcript.processing_error = ''
        transcript.save(update_fields=['processing_status', 'processing_error'])
        cached = InterviewTranscript.objects.filter(recording__audio_sha256=transcript.recording.audio_sha256, processing_status=ProcessingStatus.COMPLETED).exclude(pk=transcript.pk).order_by('-generated_at').first()
        if cached:
            transcript.transcript_text, transcript.transcript_json = cached.transcript_text, {**cached.transcript_json, 'cache_reused_from_transcript_id': cached.public_id}
        else:
            payload = transcribe_recording_payload(transcript.recording)
            transcript.transcript_text, transcript.transcript_json = payload['transcript_text'], payload['transcript_json']
        assessment = transcript.transcript_json.get('quality_assessment', {})
        transcript.processing_status = assessment.get('state', ProcessingStatus.COMPLETED)
        transcript.processing_error = '; '.join(assessment.get('reasons', [])) if transcript.processing_status == ProcessingStatus.LOW_QUALITY else ''
        # Do not resurrect a job that the stale-job guard has already failed.
        InterviewTranscript.objects.filter(
            pk=transcript_id,
            processing_status=ProcessingStatus.PROCESSING,
        ).update(
            transcript_text=transcript.transcript_text,
            transcript_json=transcript.transcript_json,
            processing_status=transcript.processing_status,
            processing_error=transcript.processing_error,
        )
    except Exception as exc:
        message = str(exc) or f'{exc.__class__.__name__}: real transcription failed.'
        logger.exception('Real transcription failed transcript=%s', transcript_id)
        InterviewTranscript.objects.filter(
            pk=transcript_id,
            processing_status__in=(ProcessingStatus.PENDING, ProcessingStatus.PROCESSING),
        ).update(processing_status=ProcessingStatus.FAILED, processing_error=message, transcript_json={'error': message, 'failed_at': timezone.now().isoformat()})
    finally:
        close_old_connections()
