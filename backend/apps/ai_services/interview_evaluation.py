"""Mock interview summary helpers and transcription compatibility wrappers."""

from decimal import Decimal

from apps.ai_services.transcription_service import (
    MOCK_TRANSCRIPT_TEXT,
    transcribe_interview_recording,
)


def generate_interview_summary(transcript):
    """Return deterministic mock AI summary data without calling GPT or external APIs."""
    strengths = 'Candidate provided clear examples and showed relevant preparation.'
    weaknesses = 'Candidate needs to provide deeper technical detail in future interviews.'
    overall_impression = 'The candidate appears suitable for continued consideration based on this mock summary.'
    return {
        'strengths': strengths,
        'weaknesses': weaknesses,
        'communication_score': Decimal('8.00'),
        'overall_impression': overall_impression,
        'editable_summary_text': (
            f'Strengths: {strengths}\n'
            f'Weaknesses: {weaknesses}\n'
            'Communication score: 8.00\n'
            f'Overall impression: {overall_impression}'
        ),
    }
