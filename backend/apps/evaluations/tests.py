"""Tests for real-result-or-clear-failure transcription guarantees."""
from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from apps.ai_services.transcription_service import (
    TranscriptionUnavailable, _cached_whisper_model, _call_local_whisper_transcription, assess_transcript_quality,
    probe_audio, run_real_transcription,
)
from apps.ai_services.speaker_diarization import (
    DiarizationUnavailable, align_transcript_segments_to_speakers, format_speaker_labelled_transcript,
    run_speaker_diarization,
)

class RealTranscriptionGuaranteeTests(SimpleTestCase):
    @patch('apps.ai_services.transcription_service.importlib.util.find_spec', return_value=None)
    def test_missing_whisper_configuration_fails_clearly(self, _available):
        with self.assertRaisesRegex(TranscriptionUnavailable, 'openai-whisper package is not installed'):
            run_real_transcription('/tmp/real-audio.wav')

    @patch('apps.ai_services.transcription_service.importlib.util.find_spec', return_value=True)
    @patch('apps.ai_services.transcription_service.importlib.import_module')
    def test_incompatible_numpy_torch_pair_fails_with_reinstall_instructions(self, import_module, _find_spec):
        fake_torch = SimpleNamespace(from_numpy=lambda _value: (_ for _ in ()).throw(RuntimeError('Numpy is not available')))
        import_module.side_effect = lambda name: {
            'whisper': SimpleNamespace(),
            'torch': fake_torch,
            'numpy': SimpleNamespace(zeros=lambda *_args, **_kwargs: [0], float32='float32'),
        }[name]

        with self.assertRaisesRegex(TranscriptionUnavailable, 'force-reinstall'):
            _cached_whisper_model('numpy-incompatibility-test')

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

    def test_quality_rejects_mixed_script_and_replacement_character_garbage(self):
        assessment = assess_transcript_quality('Hello \ufffd 你好 Привет Cymru', [{'avg_logprob': -1.5}] * 3)
        self.assertEqual(assessment['state'], 'LOW_QUALITY')
        self.assertGreater(assessment['metrics']['replacement_character_count'], 0)

    def test_quality_does_not_reject_valid_unicode_name(self):
        assessment = assess_transcript_quality('My name is José and I have worked with Django for three years.', [{'avg_logprob': -0.2}])
        self.assertEqual(assessment['state'], 'COMPLETED')

    @patch('apps.ai_services.transcription_service._cached_whisper_model')
    def test_whisper_uses_explicit_english_transcription_options(self, cached_model):
        fake_model = SimpleNamespace(transcribe=lambda *args, **kwargs: {'text': 'English text', 'segments': []})
        cached_model.return_value = (fake_model, 0.0, 'cpu')
        result = _call_local_whisper_transcription('/tmp/audio.wav', 'small')
        self.assertEqual(result['options']['language'], 'en')
        self.assertEqual(result['options']['task'], 'transcribe')
        self.assertEqual(result['options']['temperature'], 0)

    def test_overlap_alignment_uses_real_diarizer_identifiers(self):
        aligned = align_transcript_segments_to_speakers([{'start': 1, 'end': 3, 'text': 'Hello'}], [{'start_time': 0, 'end_time': 4, 'speaker_id': 'SPEAKER_07'}])
        self.assertEqual(aligned[0]['speaker_id'], 'SPEAKER_07')

    @patch.dict('os.environ', {'ENABLE_SPEAKER_DIARIZATION': 'true'}, clear=False)
    def test_diarization_without_token_returns_actionable_configuration_error(self):
        with patch.dict('os.environ', {'PYANNOTE_AUTH_TOKEN': ''}, clear=False):
            with self.assertRaisesRegex(DiarizationUnavailable, 'PYANNOTE_AUTH_TOKEN'):
                run_speaker_diarization('/tmp/audio.wav')

    @patch('apps.ai_services.transcription_service.shutil.which', return_value='/usr/bin/ffprobe')
    @patch('apps.ai_services.transcription_service.subprocess.run')
    def test_audio_probe_retains_required_ffmpeg_output_parameters(self, run, _which):
        run.return_value = SimpleNamespace(returncode=0, stdout='{"format":{"format_name":"wav"},"streams":[{"codec_type":"audio","codec_name":"pcm_s16le","sample_rate":"16000","channels":1}]}', stderr='')
        properties = probe_audio('/tmp/converted.wav')
        self.assertEqual(properties['selected_audio_codec'], 'pcm_s16le')
        self.assertEqual(properties['sample_rate'], '16000')
        self.assertEqual(properties['channels'], 1)
