"""Interview AI service compatibility wrappers."""

from apps.ai_services.transcription_service import (
    MOCK_TRANSCRIPT_TEXT,
    transcribe_interview_recording,
)
from apps.ai_services.summary_service import generate_interview_summary
