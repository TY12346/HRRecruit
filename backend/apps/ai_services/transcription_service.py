"""Interview audio transcription service with OpenAI transcription and mock fallback behavior."""

from __future__ import annotations

import importlib
import importlib.util
import mimetypes
import os
from pathlib import Path

from rest_framework.exceptions import ValidationError

from apps.ai_services.exceptions import AIServiceUnavailable
from apps.evaluations.models import ALLOWED_INTERVIEW_AUDIO_EXTENSIONS, InterviewTranscript

TRANSCRIPTION_TRUTHY_VALUES = {'1', 'true', 'yes', 'on'}
ALLOWED_AUDIO_MIME_PREFIXES = ('audio/', 'video/webm')
TRANSCRIPTION_PROVIDER_OPENAI = 'openai'
TRANSCRIPTION_PROVIDER_LOCAL_WHISPER = 'local_whisper'
TRANSCRIPTION_PROVIDER_MOCK = 'mock'
REAL_TRANSCRIPTION_PROVIDERS = {TRANSCRIPTION_PROVIDER_OPENAI, TRANSCRIPTION_PROVIDER_LOCAL_WHISPER}


class TranscriptionUnavailable(AIServiceUnavailable):
    """Raised when required real transcription cannot be used."""


def get_transcription_provider():
    """Return the configured transcription provider."""
    return os.getenv('TRANSCRIPTION_PROVIDER', TRANSCRIPTION_PROVIDER_LOCAL_WHISPER).strip().lower() or TRANSCRIPTION_PROVIDER_LOCAL_WHISPER


def use_real_transcription_enabled():
    """Return whether real ASR should run.

    Local Whisper is the default real provider. Set USE_REAL_TRANSCRIPTION=False
    or TRANSCRIPTION_PROVIDER=mock to force the local mock fallback for demos/tests.
    """
    explicit_setting = os.getenv('USE_REAL_TRANSCRIPTION')
    if explicit_setting is not None and explicit_setting.strip().lower() not in TRANSCRIPTION_TRUTHY_VALUES:
        return False
    return get_transcription_provider() in REAL_TRANSCRIPTION_PROVIDERS


def get_transcription_model():
    """Return configured ASR model name for the selected provider."""
    provider = get_transcription_provider()
    default_model = 'base' if provider == TRANSCRIPTION_PROVIDER_LOCAL_WHISPER else 'gpt-4o-transcribe'
    return os.getenv('TRANSCRIPTION_MODEL', default_model).strip() or default_model


def get_openai_api_key():
    """Return the optional OpenAI API key used only when the OpenAI provider is selected."""
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
    if not cleaned:
        raise TranscriptionUnavailable('Transcription provider returned an empty transcript.')
    return cleaned


def _extract_transcription_text(response):
    """Extract transcript text from common OpenAI SDK response shapes."""
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        return response.get('text', '')
    return getattr(response, 'text', '')


def _call_openai_transcription(audio_file, api_key, model):
    """Call OpenAI audio transcription when enabled and configured."""
    if importlib.util.find_spec('openai') is None:
        raise TranscriptionUnavailable('The OpenAI Python package is not installed; real transcription cannot run.')

    openai = importlib.import_module('openai')
    client = openai.OpenAI(api_key=api_key)
    with audio_file.open('rb') as audio_stream:
        response = client.audio.transcriptions.create(model=model, file=audio_stream)
    return _extract_transcription_text(response)


def _call_local_whisper_transcription(audio_file, model):
    """Run a local Whisper model from the openai-whisper package."""
    if importlib.util.find_spec('whisper') is None:
        raise TranscriptionUnavailable('The openai-whisper package is not installed; local Whisper transcription cannot run.')

    whisper = importlib.import_module('whisper')
    whisper_model = whisper.load_model(model)
    audio_path = getattr(audio_file, 'path', None)
    close_temporary_file = None
    if not audio_path:
        import tempfile

        suffix = Path(audio_file.name).suffix or '.audio'
        temporary_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        close_temporary_file = temporary_file.name
        with audio_file.open('rb') as audio_stream:
            for chunk in iter(lambda: audio_stream.read(1024 * 1024), b''):
                temporary_file.write(chunk)
        temporary_file.close()
        audio_path = close_temporary_file
    try:
        result = whisper_model.transcribe(audio_path)
    finally:
        if close_temporary_file:
            Path(close_temporary_file).unlink(missing_ok=True)
    return result.get('text', '') if isinstance(result, dict) else getattr(result, 'text', '')


def run_real_transcription(audio_file):
    """Run the configured real provider or raise a safe unavailability error."""
    provider = get_transcription_provider()
    model = get_transcription_model()
    try:
        if provider == TRANSCRIPTION_PROVIDER_LOCAL_WHISPER:
            transcript_text = _call_local_whisper_transcription(audio_file, model)
        elif provider == TRANSCRIPTION_PROVIDER_OPENAI:
            api_key = get_openai_api_key()
            if not api_key:
                raise TranscriptionUnavailable('OPENAI_API_KEY is required for OpenAI transcription.')
            transcript_text = _call_openai_transcription(audio_file, api_key, model)
        else:
            raise TranscriptionUnavailable(f'Unsupported transcription provider: {provider}.')
    except TranscriptionUnavailable:
        raise
    except Exception as exc:
        raise TranscriptionUnavailable(f'Real transcription failed: {exc.__class__.__name__}') from exc

    return {
        'text': post_process_transcript(transcript_text),
        'metadata': {
            'provider': provider,
            'mode': 'real',
            'model': model,
            'preprocessing': 'skipped_for_local_fyp_development',
        },
    }


def build_mock_transcription(recording, audio_file):
    """Return a deterministic local transcript for early development/demo use."""
    interview = getattr(recording, 'interview', None)
    application = getattr(interview, 'application', None)
    job = getattr(application, 'job', None)
    applicant = getattr(application, 'applicant', None)
    job_title = getattr(job, 'title', '') or 'the role'
    applicant_name = getattr(applicant, 'full_name', '') or 'the candidate'
    return {
        'text': (
            f'Mock transcript for {applicant_name} interviewing for {job_title}. '
            'The interviewer asked about relevant experience, communication, role fit, '
            'and follow-up areas for human evaluation. Replace this mock transcript with '
            'real transcription when TRANSCRIPTION_PROVIDER=local_whisper or another real provider is configured.'
        ),
        'metadata': {
            'provider': 'mock',
            'mode': 'local_development',
            'model': 'mock-transcription-v1',
            'preprocessing': 'skipped_for_local_fyp_development',
            'mock_reason': 'USE_REAL_TRANSCRIPTION is disabled or TRANSCRIPTION_PROVIDER=mock',
            'audio_file_name': audio_file.name,
        },
    }


def transcribe_recording_payload(recording):
    """Return unsaved transcript payload using real ASR only when explicitly enabled."""
    audio_file = validate_recording_audio_file(recording)
    processed_audio = preprocess_audio(audio_file)

    if use_real_transcription_enabled():
        result = run_real_transcription(processed_audio)
    else:
        result = build_mock_transcription(recording, processed_audio)
    result['metadata']['recording_id'] = recording.id

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
