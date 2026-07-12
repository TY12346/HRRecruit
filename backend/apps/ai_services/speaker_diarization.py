"""Optional speaker diarization helpers for interview transcription.

Full diarization is intentionally optional for local FYP development. Install and
configure pyannote.audio later to replace the safe not_configured fallback.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
from collections import defaultdict

from apps.ai_services.exceptions import AIServiceUnavailable

DIARIZATION_STATUS_COMPLETED = 'completed'
DIARIZATION_STATUS_UNAVAILABLE = 'unavailable'
DIARIZATION_STATUS_FAILED = 'failed'
DIARIZATION_STATUS_NOT_CONFIGURED = 'not_configured'
DISPLAY_ROLE_INTERVIEWER = 'Interviewer'
DISPLAY_ROLE_CANDIDATE = 'Candidate'
DISPLAY_ROLE_UNKNOWN = 'Unknown'
INTERVIEWER_KEYWORDS = ('manager', 'recruiter', 'interviewer', 'hr ', 'human resources', 'hiring manager')


class DiarizationUnavailable(AIServiceUnavailable):
    """Raised when optional diarization cannot run."""

    def __init__(self, message, status=DIARIZATION_STATUS_UNAVAILABLE):
        super().__init__(message)
        self.status = status


def diarization_enabled():
    return os.getenv('USE_SPEAKER_DIARIZATION', 'False').strip().lower() in {'1', 'true', 'yes', 'on'}


def _coerce_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_transcript_segments(raw_segments):
    segments = []
    for segment in raw_segments or []:
        if not isinstance(segment, dict):
            continue
        start = _coerce_float(segment.get('start_time', segment.get('start')))
        end = _coerce_float(segment.get('end_time', segment.get('end')))
        text = ' '.join(str(segment.get('text') or '').split())
        if text:
            segments.append({'start_time': start, 'end_time': end, 'text': text})
    return segments


def _load_pyannote_pipeline(pyannote_audio, model_name, token):
    """Load pyannote pipeline across supported pyannote/Hugging Face versions."""
    from_pretrained = pyannote_audio.Pipeline.from_pretrained
    if token:
        try:
            return from_pretrained(model_name, token=token)
        except TypeError as token_error:
            try:
                return from_pretrained(model_name, use_auth_token=token)
            except TypeError:
                raise token_error
    return from_pretrained(model_name)


def _format_diarization_error(exc):
    detail = str(exc).strip()
    if detail:
        return f'Speaker diarization failed: {exc.__class__.__name__}: {detail}'
    return f'Speaker diarization failed: {exc.__class__.__name__}'


def _is_torchcodec_audio_read_error(exc):
    message = str(exc).lower()
    return 'torchcodec' in message and 'cannot read audio file' in message


def _load_audio_waveform_with_whisper(audio_path):
    """Load audio through Whisper/ffmpeg for pyannote when torchcodec cannot decode it."""
    if importlib.util.find_spec('whisper') is None:
        raise DiarizationUnavailable(
            'Speaker diarization could not decode the audio because torchcodec is unavailable and openai-whisper is not installed for fallback audio loading.',
            status=DIARIZATION_STATUS_UNAVAILABLE,
        )
    if importlib.util.find_spec('torch') is None:
        raise DiarizationUnavailable(
            'Speaker diarization could not decode the audio because torch is unavailable for waveform fallback.',
            status=DIARIZATION_STATUS_UNAVAILABLE,
        )

    whisper = importlib.import_module('whisper')
    torch = importlib.import_module('torch')
    samples = whisper.load_audio(audio_path)
    waveform = torch.as_tensor(samples, dtype=torch.float32).unsqueeze(0)
    return {'waveform': waveform, 'sample_rate': 16000}


def _run_diarization_pipeline(pipeline, audio_path):
    try:
        return pipeline(audio_path)
    except RuntimeError as exc:
        if not _is_torchcodec_audio_read_error(exc):
            raise
        waveform_input = _load_audio_waveform_with_whisper(audio_path)
        return pipeline(waveform_input)


def run_speaker_diarization(audio_file):
    """Return diarized speaker turns or raise DiarizationUnavailable.

    To enable real local diarization later, install pyannote.audio, accept the
    required model terms, set USE_SPEAKER_DIARIZATION=True, and provide
    PYANNOTE_AUTH_TOKEN for the configured model.
    """
    if not diarization_enabled():
        raise DiarizationUnavailable(
            'Speaker diarization is not configured for this environment.',
            status=DIARIZATION_STATUS_NOT_CONFIGURED,
        )
    try:
        pyannote_available = importlib.util.find_spec('pyannote.audio') is not None
    except ModuleNotFoundError:
        pyannote_available = False
    if not pyannote_available:
        raise DiarizationUnavailable(
            'Speaker diarization dependencies are not installed for this environment.',
            status=DIARIZATION_STATUS_UNAVAILABLE,
        )

    token = os.getenv('PYANNOTE_AUTH_TOKEN', '').strip()
    model_name = os.getenv('DIARIZATION_MODEL', 'pyannote/speaker-diarization-3.1').strip()
    try:
        pyannote_audio = importlib.import_module('pyannote.audio')
        pipeline = _load_pyannote_pipeline(pyannote_audio, model_name, token)
        audio_path = getattr(audio_file, 'path', None)
        if not audio_path:
            raise DiarizationUnavailable(
                'Speaker diarization requires a local audio file path in this development implementation.',
                status=DIARIZATION_STATUS_UNAVAILABLE,
            )
        diarization = _run_diarization_pipeline(pipeline, audio_path)
        turns = []
        for turn, _track, speaker in diarization.itertracks(yield_label=True):
            turns.append({'speaker_id': str(speaker), 'start_time': float(turn.start), 'end_time': float(turn.end)})
        if not turns:
            raise DiarizationUnavailable(
                'Speaker diarization returned no speaker turns.',
                status=DIARIZATION_STATUS_UNAVAILABLE,
            )
        return turns
    except DiarizationUnavailable:
        raise
    except Exception as exc:
        raise DiarizationUnavailable(_format_diarization_error(exc)) from exc


def calculate_overlap(start_a, end_a, start_b, end_b):
    if None in (start_a, end_a, start_b, end_b):
        return 0.0
    return max(0.0, min(end_a, end_b) - max(start_a, start_b))


def align_transcript_segments_to_speakers(transcript_segments, speaker_turns):
    aligned = []
    for segment in normalize_transcript_segments(transcript_segments):
        best_turn = None
        best_overlap = 0.0
        for turn in speaker_turns or []:
            overlap = calculate_overlap(segment['start_time'], segment['end_time'], _coerce_float(turn.get('start_time')), _coerce_float(turn.get('end_time')))
            if overlap > best_overlap:
                best_overlap = overlap
                best_turn = turn
        speaker_id = best_turn.get('speaker_id') if best_turn else 'UNKNOWN'
        aligned.append({**segment, 'speaker_id': speaker_id or 'UNKNOWN'})
    return aligned


def map_speakers_to_roles(aligned_segments):
    stats = defaultdict(lambda: {'questions': 0, 'duration': 0.0, 'keyword_hits': 0, 'chars': 0})
    for segment in aligned_segments or []:
        speaker_id = segment.get('speaker_id') or 'UNKNOWN'
        text = str(segment.get('text') or '')
        lower_text = f' {text.lower()} '
        stats[speaker_id]['questions'] += text.count('?')
        stats[speaker_id]['chars'] += len(text)
        stats[speaker_id]['keyword_hits'] += sum(1 for keyword in INTERVIEWER_KEYWORDS if keyword in lower_text)
        start = _coerce_float(segment.get('start_time'))
        end = _coerce_float(segment.get('end_time'))
        if start is not None and end is not None and end > start:
            stats[speaker_id]['duration'] += end - start

    speaker_ids = [speaker_id for speaker_id in stats if speaker_id != 'UNKNOWN']
    if not speaker_ids:
        return {}, 'Speaker role mapping is uncertain because no diarized speakers were detected.'

    interviewer = max(speaker_ids, key=lambda sid: (stats[sid]['keyword_hits'], stats[sid]['questions'], -stats[sid]['duration']))
    mapping = {interviewer: DISPLAY_ROLE_INTERVIEWER}
    remaining = [sid for sid in speaker_ids if sid != interviewer]
    if remaining:
        candidate = max(remaining, key=lambda sid: (stats[sid]['duration'], stats[sid]['chars']))
        mapping[candidate] = DISPLAY_ROLE_CANDIDATE
        for sid in remaining:
            mapping.setdefault(sid, DISPLAY_ROLE_CANDIDATE)
        return mapping, None
    return mapping, 'Speaker role mapping is uncertain because only one speaker was detected.'


def apply_role_mapping(aligned_segments, role_mapping):
    return [{**segment, 'role': role_mapping.get(segment.get('speaker_id'), DISPLAY_ROLE_UNKNOWN)} for segment in aligned_segments or []]


def format_speaker_labelled_transcript(speaker_segments):
    paragraphs = []
    current_role = None
    current_text = []
    for segment in speaker_segments or []:
        text = ' '.join(str(segment.get('text') or '').split())
        if not text:
            continue
        role = segment.get('role') or DISPLAY_ROLE_UNKNOWN
        if role == current_role:
            current_text.append(text)
        else:
            if current_role and current_text:
                paragraphs.append(f'{current_role}: {" ".join(current_text)}')
            current_role = role
            current_text = [text]
    if current_role and current_text:
        paragraphs.append(f'{current_role}: {" ".join(current_text)}')
    return '\n\n'.join(paragraphs)


def build_transcript_json_payload(plain_transcript, speaker_labelled_transcript, diarization_status, diarization_warning, segments, metadata=None):
    return {
        **(metadata or {}),
        'plain_transcript': plain_transcript,
        'speaker_labelled_transcript': speaker_labelled_transcript,
        'diarization_status': diarization_status,
        'diarization_warning': diarization_warning,
        'segments': segments or [],
    }
