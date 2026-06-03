"""Mock interview transcription and summary helpers for FYP development."""

from decimal import Decimal

MOCK_TRANSCRIPT_TEXT = 'This is a mock transcript for FYP development.'


def transcribe_interview_recording(recording):
    """Return deterministic mock transcript data without calling Whisper or external APIs."""
    return {
        'transcript_text': MOCK_TRANSCRIPT_TEXT,
        'transcript_json': {
            'provider': 'mock',
            'recording_id': recording.id,
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
