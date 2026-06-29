"""Interview AI summary service with strict real-LLM behavior.

The current backend stores and validates ``communication_score`` on a 0-10 scale.
This service preserves that scale for API compatibility instead of adopting the
0-100 example value shown in the algorithm document. Any future scale migration
must update model validation, serializers, frontend labels, tests, and reports
together.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
from decimal import Decimal, InvalidOperation

from apps.ai_services.exceptions import AIServiceUnavailable

SUMMARY_TRUTHY_VALUES = {'1', 'true', 'yes', 'on'}

SUMMARY_REQUIRED_FIELDS = {
    'strengths',
    'weaknesses',
    'communication_score',
    'overall_impression',
    'editable_summary_text',
}
COMMUNICATION_SCORE_MIN = Decimal('0.00')
COMMUNICATION_SCORE_MAX = Decimal('10.00')
SUMMARY_TRANSPARENCY_VERSION = 'interview-summary-transparency-v1'


def build_summary_transparency_metadata(
    cleaned_transcript,
    provider,
    model='',
    generation_mode='real_llm',
):
    """Build recruiter/interviewer-facing metadata explaining how a summary was produced."""
    excerpt = cleaned_transcript[:500]
    if len(cleaned_transcript) > 500:
        excerpt = f'{excerpt}…'
    return {
        'transparency_version': SUMMARY_TRANSPARENCY_VERSION,
        'provider': provider,
        'model': model,
        'generation_mode': generation_mode,
        'source': 'interview_transcript',
        'source_excerpt': excerpt,
        'human_review_required': True,
        'decision_boundary': 'This AI summary supports interviewer review only and must not be treated as a final hiring decision.',
        'editable_fields': sorted(SUMMARY_REQUIRED_FIELDS),
        'limitations': [
            'May miss context from audio tone, body language, or incomplete transcripts.',
            'May contain summarization mistakes; interviewer must verify against the transcript.',
            "Communication score is a decision-support signal on HRRecruit's current 0-10 scale.",
        ],
    }


class SummaryGenerationUnavailable(AIServiceUnavailable):
    """Raised when required real summary generation cannot be used."""


def use_real_summary_enabled():
    """Return whether real LLM summary generation is enabled by environment variable."""
    return os.getenv('USE_REAL_SUMMARY', 'False').strip().lower() in SUMMARY_TRUTHY_VALUES


def get_summary_model():
    """Return the configured optional summary model name."""
    return os.getenv('SUMMARY_MODEL', 'gpt-4o-mini').strip() or 'gpt-4o-mini'


def get_openai_api_key():
    """Return the optional OpenAI API key used only when real summary is enabled."""
    return os.getenv('OPENAI_API_KEY', '').strip()


def preprocess_transcript_text(transcript):
    """Normalize transcript text before prompting the configured summary model."""
    raw_text = getattr(transcript, 'transcript_text', transcript)
    return ' '.join(str(raw_text or '').split())


def build_structured_summary_prompt(cleaned_transcript):
    """Construct a structured prompt that asks the provider for editable JSON only."""
    return (
        'You are assisting an interviewer in an HRRecruit interview workflow. '
        'Summarize the transcript to support human evaluation only. Do not make '
        'hiring, rejection, approval, or final decision recommendations.\n\n'
        'Return valid JSON with exactly these fields: strengths, weaknesses, '
        'communication_score, overall_impression, editable_summary_text. '
        'Use a communication_score from 0 to 10 because the current HRRecruit '
        'interview summary model and UI use a 0-10 scale. Keep the text concise, '
        'professional, and editable by the interviewer.\n\n'
        f'Interview transcript:\n{cleaned_transcript}'
    )


def _extract_message_content(response):
    """Extract model content from common OpenAI SDK response shapes."""
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        choices = response.get('choices') or []
        if choices:
            message = choices[0].get('message') or {}
            return message.get('content', '')
        return response.get('content', '')

    choices = getattr(response, 'choices', None) or []
    if choices:
        message = getattr(choices[0], 'message', None)
        return getattr(message, 'content', '') if message is not None else ''
    return getattr(response, 'content', '')


def _parse_summary_content(content):
    """Parse provider JSON content into a dictionary."""
    if isinstance(content, dict):
        return content
    if not isinstance(content, str) or not content.strip():
        raise SummaryGenerationUnavailable('Summary provider returned an empty response.')

    text = content.strip()
    if text.startswith('```'):
        text = text.strip('`').strip()
        if text.lower().startswith('json'):
            text = text[4:].strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SummaryGenerationUnavailable('Summary provider returned invalid JSON.') from exc
    if not isinstance(parsed, dict):
        raise SummaryGenerationUnavailable('Summary provider JSON response must be an object.')
    return parsed


def _coerce_communication_score(value):
    """Coerce and validate the current 0-10 communication score scale."""
    try:
        score = Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise SummaryGenerationUnavailable('Summary provider returned an invalid communication_score.') from exc

    if score < COMMUNICATION_SCORE_MIN or score > COMMUNICATION_SCORE_MAX:
        raise SummaryGenerationUnavailable('Summary provider communication_score must be between 0 and 10.')
    return score


def validate_structured_summary(summary):
    """Validate and post-process summary output for storage."""
    missing_fields = SUMMARY_REQUIRED_FIELDS - set(summary.keys())
    if missing_fields:
        missing = ','.join(sorted(missing_fields))
        raise SummaryGenerationUnavailable(f'Summary provider response is missing required field(s): {missing}.')

    cleaned_summary = {
        'strengths': str(summary.get('strengths') or '').strip(),
        'weaknesses': str(summary.get('weaknesses') or '').strip(),
        'communication_score': _coerce_communication_score(summary.get('communication_score')),
        'overall_impression': str(summary.get('overall_impression') or '').strip(),
        'editable_summary_text': str(summary.get('editable_summary_text') or '').strip(),
    }
    empty_text_fields = [
        field for field in SUMMARY_REQUIRED_FIELDS - {'communication_score'} if not cleaned_summary[field]
    ]
    if empty_text_fields:
        empty = ','.join(sorted(empty_text_fields))
        raise SummaryGenerationUnavailable(f'Summary provider response contains empty required field(s): {empty}.')
    if isinstance(summary.get('summary_json'), dict):
        cleaned_summary['summary_json'] = summary['summary_json']
    return cleaned_summary


def _call_openai_summary(prompt, api_key, model):
    """Call OpenAI only when explicitly enabled and configured."""
    if importlib.util.find_spec('openai') is None:
        raise SummaryGenerationUnavailable('The OpenAI Python package is not installed; real summary generation cannot run.')

    openai = importlib.import_module('openai')
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                'role': 'system',
                'content': 'Return strict JSON for an editable interview summary. Do not make hiring decisions.',
            },
            {'role': 'user', 'content': prompt},
        ],
        response_format={'type': 'json_object'},
        temperature=0.2,
    )
    return _extract_message_content(response)


def run_real_summary(cleaned_transcript):
    """Run real LLM summary generation or raise a clear unavailability error."""
    api_key = get_openai_api_key()
    if not api_key:
        raise SummaryGenerationUnavailable('OPENAI_API_KEY is required for real summary generation.')

    model = get_summary_model()
    prompt = build_structured_summary_prompt(cleaned_transcript)
    try:
        content = _call_openai_summary(prompt, api_key, model)
        parsed = _parse_summary_content(content)
        parsed['summary_json'] = build_summary_transparency_metadata(
            cleaned_transcript,
            provider='openai',
            model=model,
            generation_mode='real_llm',
        )
        return validate_structured_summary(parsed)
    except SummaryGenerationUnavailable:
        raise
    except Exception as exc:
        raise SummaryGenerationUnavailable(f'Real summary generation failed: {exc.__class__.__name__}') from exc


def generate_summary_payload(transcript):
    """Return unsaved structured summary payload for a transcript."""
    cleaned_transcript = preprocess_transcript_text(transcript)

    if not use_real_summary_enabled():
        raise SummaryGenerationUnavailable('Real summary generation is disabled. Set USE_REAL_SUMMARY=True and configure OPENAI_API_KEY.')
    return run_real_summary(cleaned_transcript)


# Compatibility name for older imports/tests.
def generate_interview_summary(transcript):
    """Return structured interview summary data without saving."""
    return generate_summary_payload(transcript)
