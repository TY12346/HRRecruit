"""Real, profiled interview transcription with cached local Whisper models."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import logging
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from time import perf_counter

from rest_framework.exceptions import ValidationError

from apps.ai_services.exceptions import AIServiceUnavailable
from apps.ai_services.speaker_diarization import (
    DIARIZATION_STATUS_COMPLETED, DIARIZATION_STATUS_FAILED, DIARIZATION_STATUS_NOT_CONFIGURED,
    DIARIZATION_STATUS_UNAVAILABLE, DiarizationUnavailable, align_transcript_segments_to_speakers,
    build_transcript_json_payload, format_speaker_labelled_transcript, normalize_transcript_segments,
    run_speaker_diarization,
)
from apps.evaluations.models import ALLOWED_INTERVIEW_AUDIO_EXTENSIONS, InterviewTranscript

logger = logging.getLogger(__name__)
TRANSCRIPTION_PROVIDER_OPENAI = 'openai'
TRANSCRIPTION_PROVIDER_LOCAL_WHISPER = 'local_whisper'
_MODEL_CACHE, _MODEL_LOCK = {}, threading.Lock()

class TranscriptionUnavailable(AIServiceUnavailable):
    """Raised when a real transcription provider cannot produce a result."""

def _enabled(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}

def get_transcription_provider():
    return os.getenv('TRANSCRIPTION_PROVIDER', TRANSCRIPTION_PROVIDER_LOCAL_WHISPER).strip().lower() or TRANSCRIPTION_PROVIDER_LOCAL_WHISPER

def get_transcription_model():
    default = 'base' if get_transcription_provider() == TRANSCRIPTION_PROVIDER_LOCAL_WHISPER else 'gpt-4o-transcribe'
    return os.getenv('WHISPER_MODEL_SIZE', os.getenv('TRANSCRIPTION_MODEL', default)).strip() or default

def get_openai_api_key(): return os.getenv('OPENAI_API_KEY', '').strip()

def validate_recording_audio_file(recording):
    audio_file = recording.audio_file
    if not audio_file or not audio_file.name or not audio_file.storage.exists(audio_file.name):
        raise ValidationError({'audio_file': 'Interview recording audio file is missing or does not exist.'})
    if Path(audio_file.name).suffix.lstrip('.').lower() not in ALLOWED_INTERVIEW_AUDIO_EXTENSIONS:
        raise ValidationError({'audio_file': 'Unsupported interview audio file type.'})
    return audio_file

def file_sha256(audio_file):
    digest = hashlib.sha256()
    with audio_file.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): digest.update(block)
    return digest.hexdigest()

def preprocess_audio(audio_file):
    """Convert real input to 16kHz mono PCM WAV; never substitutes audio."""
    if not shutil.which('ffmpeg'):
        raise TranscriptionUnavailable('ffmpeg is required to preprocess audio to 16kHz mono WAV.')
    source = getattr(audio_file, 'path', None)
    cleanup_source = None
    if not source:
        suffix = Path(audio_file.name).suffix or '.audio'
        handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        cleanup_source = handle.name
        with audio_file.open('rb') as stream: shutil.copyfileobj(stream, handle)
        handle.close(); source = cleanup_source
    output = tempfile.NamedTemporaryFile(suffix='.wav', delete=False); output.close()
    try:
        completed = subprocess.run(['ffmpeg', '-y', '-i', source, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', output.name], capture_output=True, text=True, timeout=300)
        if completed.returncode:
            raise TranscriptionUnavailable(f'Audio preprocessing failed: {completed.stderr.strip()[-500:]}')
        return output.name
    finally:
        if cleanup_source: Path(cleanup_source).unlink(missing_ok=True)

def _cached_whisper_model(model_name):
    if importlib.util.find_spec('whisper') is None: raise TranscriptionUnavailable('The openai-whisper package is not installed; local Whisper transcription cannot run.')
    with _MODEL_LOCK:
        if model_name in _MODEL_CACHE: return _MODEL_CACHE[model_name], 0.0, _MODEL_CACHE[model_name]._hrrecruit_device
        whisper = importlib.import_module('whisper')
        device = 'cpu'
        if importlib.util.find_spec('torch'):
            torch = importlib.import_module('torch')
            if torch.cuda.is_available(): device = 'cuda'
        started = perf_counter(); instance = whisper.load_model(model_name, device=device); elapsed = perf_counter() - started
        instance._hrrecruit_device = device
        _MODEL_CACHE[model_name] = instance
        return instance, elapsed, device

def post_process_transcript(text):
    cleaned = ' '.join(str(text or '').split())
    if not cleaned: raise TranscriptionUnavailable('Transcription provider returned an empty transcript.')
    return cleaned

def _call_local_whisper_transcription(audio_path, model):
    whisper_model, load_seconds, device = _cached_whisper_model(model)
    started = perf_counter(); result = whisper_model.transcribe(audio_path, fp16=(device == 'cuda'), verbose=False); seconds = perf_counter() - started
    return {'text': result.get('text', ''), 'segments': normalize_transcript_segments(result.get('segments') or []), 'model_load_seconds': load_seconds, 'transcription_seconds': seconds, 'device': device}

def run_real_transcription(audio_path):
    provider, model = get_transcription_provider(), get_transcription_model()
    if provider != TRANSCRIPTION_PROVIDER_LOCAL_WHISPER:
        raise TranscriptionUnavailable('Only configured real local Whisper transcription is supported by this processing pipeline.')
    try: result = _call_local_whisper_transcription(audio_path, model)
    except TranscriptionUnavailable: raise
    except Exception as exc: raise TranscriptionUnavailable(f'Real transcription failed: {exc.__class__.__name__}: {exc}') from exc
    return {'text': post_process_transcript(result['text']), 'segments': result['segments'], 'metadata': {'provider': provider, 'mode': 'real', 'model': model, 'device': result['device'], 'model_load_seconds': round(result['model_load_seconds'], 3), 'transcription_seconds': round(result['transcription_seconds'], 3)}}

def build_speaker_aware_transcript_payload(plain_transcript, transcript_segments, audio_path, metadata):
    enabled = _enabled('ENABLE_SPEAKER_DIARIZATION', _enabled('USE_SPEAKER_DIARIZATION'))
    diarization_status = DIARIZATION_STATUS_NOT_CONFIGURED; warning = 'Speaker separation is disabled by configuration.'; labelled = None; speaker_segments = []
    if enabled:
        started = perf_counter()
        try:
            turns = run_speaker_diarization(audio_path)
            speaker_segments = align_transcript_segments_to_speakers(transcript_segments, turns)
            if any(s['speaker_id'] == 'UNKNOWN' for s in speaker_segments): raise DiarizationUnavailable('Diarization could not align every transcript segment.', status=DIARIZATION_STATUS_FAILED)
            labelled = format_speaker_labelled_transcript(speaker_segments); diarization_status = DIARIZATION_STATUS_COMPLETED; warning = None
        except DiarizationUnavailable as exc: diarization_status, warning = exc.status, str(exc)
        except Exception as exc: diarization_status, warning = DIARIZATION_STATUS_FAILED, f'Speaker diarization failed: {exc.__class__.__name__}: {exc}'
        metadata['diarization_seconds'] = round(perf_counter() - started, 3)
    if enabled and diarization_status != DIARIZATION_STATUS_COMPLETED:
        # A valid plain transcript remains real, while the failure is explicitly recorded.
        metadata['diarization_error'] = warning
    metadata['diarization_status'] = diarization_status
    return {'transcript_text': labelled or plain_transcript, 'transcript_json': build_transcript_json_payload(plain_transcript, labelled, diarization_status, warning, speaker_segments, metadata)}

def transcribe_recording_payload(recording):
    audio = validate_recording_audio_file(recording); total = perf_counter(); pre = perf_counter(); path = preprocess_audio(audio); pre_seconds = perf_counter() - pre
    try:
        result = run_real_transcription(path); metadata = {**result['metadata'], 'recording_id': recording.id, 'audio_sha256': recording.audio_sha256, 'audio_file_save_seconds': recording.upload_seconds, 'preprocessing': 'ffmpeg_16khz_mono_pcm_wav', 'preprocessing_seconds': round(pre_seconds, 3)}
        payload = build_speaker_aware_transcript_payload(result['text'], result['segments'], path, metadata)
        payload['transcript_json']['total_processing_seconds'] = round(perf_counter() - total, 3)
        logger.info('Real transcription completed recording=%s timings=%s', recording.id, payload['transcript_json'])
        return payload
    finally: Path(path).unlink(missing_ok=True)

def transcribe_interview_recording(recording): return transcribe_recording_payload(recording)
