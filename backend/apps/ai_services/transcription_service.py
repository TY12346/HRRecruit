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
import json
import unicodedata
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
    default = 'small' if get_transcription_provider() == TRANSCRIPTION_PROVIDER_LOCAL_WHISPER else 'gpt-4o-transcribe'
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

def probe_audio(path):
    """Return selected stream and format facts used to audit real conversion."""
    if not shutil.which('ffprobe'):
        raise TranscriptionUnavailable('ffprobe is required to verify audio conversion parameters.')
    completed = subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)], capture_output=True, text=True, timeout=60)
    if completed.returncode:
        raise TranscriptionUnavailable(f'Audio inspection failed: {completed.stderr.strip()[-500:]}')
    payload = json.loads(completed.stdout)
    audio_streams = [stream for stream in payload.get('streams', []) if stream.get('codec_type') == 'audio']
    if not audio_streams:
        raise TranscriptionUnavailable('The uploaded file has no audio stream.')
    selected = audio_streams[0]
    return {'format_name': payload.get('format', {}).get('format_name'), 'duration_seconds': payload.get('format', {}).get('duration'), 'bit_rate': payload.get('format', {}).get('bit_rate'), 'audio_stream_count': len(audio_streams), 'selected_audio_codec': selected.get('codec_name'), 'sample_rate': selected.get('sample_rate'), 'channels': selected.get('channels')}

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
        completed = subprocess.run(['ffmpeg', '-y', '-i', source, '-map', '0:a:0', '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', output.name], capture_output=True, text=True, timeout=300)
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
    options = {'task': 'transcribe', 'language': 'en', 'temperature': 0, 'fp16': device == 'cuda', 'verbose': False}
    started = perf_counter(); result = whisper_model.transcribe(audio_path, **options); seconds = perf_counter() - started
    return {'text': result.get('text', ''), 'segments': result.get('segments') or [], 'model_load_seconds': load_seconds, 'transcription_seconds': seconds, 'device': device, 'options': options, 'detected_language': result.get('language')}

def _segment_diagnostics(raw_segments):
    diagnostics = []
    for segment in raw_segments:
        diagnostics.append({key: segment.get(key) for key in ('id', 'start', 'end', 'text', 'avg_logprob', 'no_speech_prob', 'compression_ratio') if key in segment})
    return diagnostics

def assess_transcript_quality(text, raw_segments):
    """Reject likely decoding garbage using several signals, while allowing names and occasional foreign words."""
    reasons, clean = [], str(text or '')
    chars = [char for char in clean if not char.isspace()]
    replacement_count = clean.count('\ufffd')
    if replacement_count:
        reasons.append('Transcript contains Unicode replacement characters produced before storage.')
    if chars:
        non_latin = sum(unicodedata.category(char).startswith('L') and not ('LATIN' in unicodedata.name(char, '') or char.isascii()) for char in chars)
        if non_latin / len(chars) > 0.12:
            reasons.append('Transcript contains an implausibly high proportion of non-Latin script for an English interview.')
    normalized = ' '.join(clean.lower().split())
    words = normalized.split()
    if len(words) >= 12 and len(set(words)) <= max(2, len(words) // 5):
        reasons.append('Transcript has suspiciously repetitive decoding output.')
    segments = list(raw_segments or [])
    low_confidence = [s for s in segments if s.get('avg_logprob') is not None and s['avg_logprob'] < -1.2]
    no_speech = [s for s in segments if s.get('no_speech_prob') is not None and s['no_speech_prob'] > 0.75]
    compressed = [s for s in segments if s.get('compression_ratio') is not None and s['compression_ratio'] > 2.4]
    if len(segments) >= 3 and len(low_confidence) / len(segments) >= 0.7:
        reasons.append('Most Whisper segments have low average log probability.')
    if len(segments) >= 3 and len(no_speech) / len(segments) >= 0.7:
        reasons.append('Most Whisper segments are classified as no speech.')
    if len(segments) >= 3 and len(compressed) / len(segments) >= 0.5:
        reasons.append('Many Whisper segments have a high compression ratio, indicating repetitive decoding.')
    return {'state': 'LOW_QUALITY' if reasons else 'COMPLETED', 'reasons': reasons, 'metrics': {'replacement_character_count': replacement_count, 'segment_count': len(segments), 'low_confidence_segment_count': len(low_confidence), 'no_speech_segment_count': len(no_speech), 'high_compression_segment_count': len(compressed)}}

def run_real_transcription(audio_path):
    provider, model = get_transcription_provider(), get_transcription_model()
    if provider != TRANSCRIPTION_PROVIDER_LOCAL_WHISPER:
        raise TranscriptionUnavailable('Only configured real local Whisper transcription is supported by this processing pipeline.')
    try: result = _call_local_whisper_transcription(audio_path, model)
    except TranscriptionUnavailable: raise
    except Exception as exc: raise TranscriptionUnavailable(f'Real transcription failed: {exc.__class__.__name__}: {exc}') from exc
    text = post_process_transcript(result['text'])
    return {'text': text, 'segments': normalize_transcript_segments(result['segments']), 'metadata': {'provider': provider, 'mode': 'real', 'model': model, 'device': result['device'], 'model_load_seconds': round(result['model_load_seconds'], 3), 'transcription_seconds': round(result['transcription_seconds'], 3), 'language': 'en', 'detected_language': result['detected_language'], 'transcription_options': result['options'], 'whisper_segments': _segment_diagnostics(result['segments']), 'quality_assessment': assess_transcript_quality(text, result['segments'])}}

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
    audio = validate_recording_audio_file(recording); total = perf_counter(); source_path = getattr(audio, 'path', None); source_properties = probe_audio(source_path) if source_path else None; path = None; pre = perf_counter(); path = preprocess_audio(audio); pre_seconds = perf_counter() - pre
    try:
        converted_properties = probe_audio(path)
        if converted_properties['selected_audio_codec'] != 'pcm_s16le' or converted_properties['sample_rate'] != '16000' or converted_properties['channels'] != 1:
            raise TranscriptionUnavailable('Audio conversion verification failed: Whisper input is not PCM signed 16-bit little-endian, 16 kHz, mono WAV.')
        result = run_real_transcription(path); metadata = {**result['metadata'], 'recording_id': recording.id, 'audio_sha256': recording.audio_sha256, 'audio_file_save_seconds': recording.upload_seconds, 'source_audio_properties': source_properties, 'whisper_input_properties': converted_properties, 'preprocessing': 'ffmpeg_16khz_mono_pcm_wav', 'preprocessing_seconds': round(pre_seconds, 3)}
        payload = build_speaker_aware_transcript_payload(result['text'], result['segments'], path, metadata)
        payload['transcript_json']['total_processing_seconds'] = round(perf_counter() - total, 3)
        logger.info('Real transcription completed recording=%s timings=%s', recording.id, payload['transcript_json'])
        return payload
    finally:
        if path and not _enabled('PRESERVE_PREPROCESSED_AUDIO', False): Path(path).unlink(missing_ok=True)

def transcribe_interview_recording(recording): return transcribe_recording_payload(recording)
