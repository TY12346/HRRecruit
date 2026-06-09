"""Interview audio transcription service with mock-first FYP fallback behavior."""

from __future__ import annotations

import importlib
import importlib.util
import mimetypes
import os
from pathlib import Path

from rest_framework.exceptions import ValidationError

from apps.evaluations.models import ALLOWED_INTERVIEW_AUDIO_EXTENSIONS, InterviewTranscript

MOCK_TRANSCRIPT_TEXT = 'This is a mock interview transcript for FYP development.'
TRANSCRIPTION_TRUTHY_VALUES = {'1', 'true', 'yes', 'on'}
ALLOWED_AUDIO_MIME_PREFIXES = ('audio/', 'video/webm')


class TranscriptionUnavailable(Exception):
    """Raised when optional real transcription cannot be used safely."""


def use_real_transcription_enabled():
    """Return whether real ASR is enabled by environment variable."""
    return os.getenv('USE_REAL_TRANSCRIPTION', 'False').strip().lower() in TRANSCRIPTION_TRUTHY_VALUES


def get_transcription_model():
    """Return configured ASR model name, defaulting to Whisper for optional OpenAI use."""
    return os.getenv('TRANSCRIPTION_MODEL', 'whisper-1').strip() or 'whisper-1'


def get_openai_api_key():
    """Return the optional OpenAI API key used only when real transcription is enabled."""
    return os.getenv('OPENAI_API_KEY', '').strip()


def validate_recording_audio_file(recording):
    """Validate the recording has an existing audio file with an allowed extension/type."""
    audio_file = getattr(recording, 'audio_file', None)
    if not audio_file or not getattr(audio_file, 'name', ''):
        raise ValidationError({'audio_file': 'Interview recording audio file is missing.'})

    storage = audio_file.storage
    if not storage.exists(audio_file.name):
        raise ValidationError({'audio_file': 'Interview recording audio file does not exist.'})

    extension = Path(audio_file.name).suffix.lstrip('.').lower()
    if extension not in ALLOWED_INTERVIEW_AUDIO_EXTENSIONS:
        allowed = ', '.join(ALLOWED_INTERVIEW_AUDIO_EXTENSIONS)
        raise ValidationError({'audio_file': f'Unsupported audio file type. Allowed extensions: {allowed}.'})

    guessed_type, _ = mimetypes.guess_type(audio_file.name)
    if guessed_type and not guessed_type.startswith(ALLOWED_AUDIO_MIME_PREFIXES):
        raise ValidationError({'audio_file': 'Unsupported audio content type.'})

    return audio_file


def preprocess_audio(audio_file):
    """Return audio unchanged; preprocessing is skipped for local FYP development."""
    return audio_file


def post_process_transcript(transcript_text):
    """Normalize provider transcript text before saving."""
    cleaned = ' '.join(str(transcript_text or '').split())
    return cleaned or MOCK_TRANSCRIPT_TEXT


def build_mock_transcription(recording, reason):
    """Build deterministic mock transcript payload and provider metadata."""
    return {
        'text': MOCK_TRANSCRIPT_TEXT,
        'metadata': {
            'provider': 'mock',
            'mode': 'fallback',
            'fallback_reason': reason,
            'recording_id': recording.id,
            'preprocessing': 'skipped_for_local_fyp_development',
            'segments': [
                {
                    'speaker': 'candidate',
                    'start_seconds': 0,
                    'end_seconds': 5,
                    'text': MOCK_TRANSCRIPT_TEXT,
                }
            ],
        },
    }


def _extract_transcription_text(response):
    """Extract transcript text from common OpenAI SDK response shapes."""
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        return response.get('text', '')
    return getattr(response, 'text', '')


def _call_openai_transcription(audio_file, api_key, model):
    """Call OpenAI Whisper transcription when explicitly enabled and configured."""
    if importlib.util.find_spec('openai') is None:
        raise TranscriptionUnavailable('openai_package_unavailable')

    openai = importlib.import_module('openai')
    client = openai.OpenAI(api_key=api_key)
    with audio_file.open('rb') as audio_stream:
        response = client.audio.transcriptions.create(model=model, file=audio_stream)
    return _extract_transcription_text(response)


def run_real_transcription(audio_file):
    """Run optional real provider or raise a safe unavailability error."""
    api_key = get_openai_api_key()
    if not api_key:
        raise TranscriptionUnavailable('missing_openai_api_key')

    model = get_transcription_model()
    try:
        transcript_text = _call_openai_transcription(audio_file, api_key, model)
    except TranscriptionUnavailable:
        raise
    except Exception as exc:
        raise TranscriptionUnavailable(f'real_transcription_failed: {exc.__class__.__name__}') from exc

    return {
        'text': post_process_transcript(transcript_text),
        'metadata': {
            'provider': 'openai',
            'mode': 'real',
            'model': model,
            'preprocessing': 'skipped_for_local_fyp_development',
        },
    }


def transcribe_recording_payload(recording):
    """Return unsaved transcript payload for compatibility with existing callers."""
    audio_file = validate_recording_audio_file(recording)
    processed_audio = preprocess_audio(audio_file)

    if not use_real_transcription_enabled():
        result = build_mock_transcription(recording, 'real_transcription_disabled')
    else:
        try:
            result = run_real_transcription(processed_audio)
            result['metadata']['recording_id'] = recording.id
        except TranscriptionUnavailable as exc:
            result = build_mock_transcription(recording, str(exc))

    cleaned_text = post_process_transcript(result['text'])
    metadata = {
        **result['metadata'],
        'algorithm': 'automatic_speech_recognition',
        'audio_file_name': audio_file.name,
        'post_processing': 'collapsed_whitespace_and_trimmed',
    }
    return {
        'transcript_text': cleaned_text,
        'transcript_json': metadata,
    }


def transcribe_and_save_recording(recording):
    """Transcribe a recording, save the transcript, and return the transcript instance."""
    payload = transcribe_recording_payload(recording)
    return InterviewTranscript.objects.create(recording=recording, **payload)


# Compatibility wrapper for existing imports/tests that expect this function name.
def transcribe_interview_recording(recording):
    """Return transcript payload without saving, preserving existing service API shape."""
    return transcribe_recording_payload(recording)
