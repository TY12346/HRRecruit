"""Tests for real-result-or-clear-failure transcription guarantees."""
from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from apps.ai_services.transcription_service import TranscriptionUnavailable, run_real_transcription
from apps.ai_services.speaker_diarization import format_speaker_labelled_transcript

class RealTranscriptionGuaranteeTests(SimpleTestCase):
    @patch('apps.ai_services.transcription_service.importlib.util.find_spec', return_value=None)
    def test_missing_whisper_configuration_fails_clearly(self, _available):
        with self.assertRaisesRegex(TranscriptionUnavailable, 'openai-whisper package is not installed'):
            run_real_transcription('/tmp/real-audio.wav')

    def test_diarizer_output_never_invents_participant_roles(self):
        rendered = format_speaker_labelled_transcript([{'speaker_id': 'SPEAKER_00', 'text': 'Real words'}])
        self.assertEqual(rendered, 'SPEAKER_00: Real words')
        self.assertNotIn('Interviewer:', rendered)
        self.assertNotIn('Applicant:', rendered)

    @override_settings(STRICT_REAL_AI=True, ALLOW_MOCK_AI=False)
    def test_strict_mode_does_not_provide_mock_transcription(self):
        with self.assertRaises(TranscriptionUnavailable):
            with patch('apps.ai_services.transcription_service.importlib.util.find_spec', return_value=None):
                run_real_transcription('/tmp/real-audio.wav')
