"""Serializers for interview recordings, transcripts, summaries, and evaluations."""

from decimal import Decimal
from time import perf_counter
from apps.ai_services.transcription_service import file_sha256

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.applications.models import JobApplication
from apps.jobs.serializers import EvaluationCriterionSerializer
from .deliverables import deliverable_deadline_for
from apps.common.serializers import ReadableIdModelSerializer

from .models import (
    ALLOWED_INTERVIEW_AUDIO_EXTENSIONS,
    MAX_INTERVIEW_AUDIO_SIZE_MB,
    EvaluationAnswer,
    InterviewAISummary,
    InterviewEvaluation,
    InterviewRecording,
    InterviewTranscript,
    validate_interview_audio_size,
)

ALLOWED_INTERVIEW_AUDIO_CONTENT_TYPES = {
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/x-wav',
    'audio/mp4',
    'audio/m4a',
    'audio/ogg',
    'audio/webm',
    'audio/aac',
    'video/webm',
}


class InterviewRecordingSerializer(ReadableIdModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)

    class Meta:
        model = InterviewRecording
        fields = ['id', 'interview', 'audio_file', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['id', 'interview', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']


class InterviewRecordingUploadSerializer(ReadableIdModelSerializer):
    class Meta:
        model = InterviewRecording
        fields = ['audio_file']

    def validate_audio_file(self, audio_file):
        extension = audio_file.name.rsplit('.', 1)[-1].lower() if '.' in audio_file.name else ''
        if extension not in ALLOWED_INTERVIEW_AUDIO_EXTENSIONS:
            allowed = ', '.join(ALLOWED_INTERVIEW_AUDIO_EXTENSIONS)
            raise serializers.ValidationError(f'Unsupported audio file type. Allowed extensions: {allowed}.')

        content_type = getattr(audio_file, 'content_type', '')
        if content_type and content_type not in ALLOWED_INTERVIEW_AUDIO_CONTENT_TYPES:
            raise serializers.ValidationError('Unsupported audio content type.')

        try:
            validate_interview_audio_size(audio_file)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return audio_file

    def create(self, validated_data):
        started = perf_counter()
        recording = InterviewRecording.objects.create(interview=self.context['interview'], uploaded_by=self.context['request'].user, **validated_data)
        recording.audio_sha256 = file_sha256(recording.audio_file)
        recording.upload_seconds = round(perf_counter() - started, 3)
        recording.save(update_fields=['audio_sha256', 'upload_seconds'])
        return recording


class InterviewTranscriptSerializer(ReadableIdModelSerializer):
    audio_url = serializers.SerializerMethodField()
    transcript = serializers.SerializerMethodField()
    speaker_labelled_transcript = serializers.SerializerMethodField()
    speaker_segments = serializers.SerializerMethodField()
    diarization_status = serializers.SerializerMethodField()
    diarization_warning = serializers.SerializerMethodField()

    class Meta:
        model = InterviewTranscript
        fields = [
            'id',
            'recording',
            'audio_url',
            'transcript_text',
            'transcript_json',
            'generated_at',
            'processing_status',
            'processing_error',
            'transcript',
            'speaker_labelled_transcript',
            'speaker_segments',
            'diarization_status',
            'diarization_warning',
        ]
        read_only_fields = fields

    def get_audio_url(self, obj):
        if not obj.recording.audio_file:
            return None
        request = self.context.get('request')
        url = obj.recording.audio_file.url
        return request.build_absolute_uri(url) if request else url

    def _metadata(self, obj):
        return obj.transcript_json or {}

    def get_transcript(self, obj):
        return self._metadata(obj).get('plain_transcript') or obj.transcript_text

    def get_speaker_labelled_transcript(self, obj):
        return self._metadata(obj).get('speaker_labelled_transcript')

    def get_speaker_segments(self, obj):
        return self._metadata(obj).get('segments') or []

    def get_diarization_status(self, obj):
        return self._metadata(obj).get('diarization_status', 'unavailable')

    def get_diarization_warning(self, obj):
        return self._metadata(obj).get('diarization_warning')


class InterviewAISummarySerializer(ReadableIdModelSerializer):
    edited_by_name = serializers.CharField(source='edited_by.full_name', read_only=True)
    transparency = serializers.SerializerMethodField()

    class Meta:
        model = InterviewAISummary
        fields = [
            'id',
            'transcript',
            'strengths',
            'weaknesses',
            'communication_score',
            'overall_impression',
            'editable_summary_text',
            'summary_json',
            'transparency',
            'edited_by',
            'edited_by_name',
            'generated_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'transcript', 'summary_json', 'transparency', 'edited_by', 'edited_by_name', 'generated_at', 'updated_at']

    def get_transparency(self, obj):
        metadata = obj.summary_json or {}
        return {
            'provider': metadata.get('provider', 'unknown'),
            'model': metadata.get('model', ''),
            'generation_mode': metadata.get('generation_mode', 'unknown'),
            'human_review_required': metadata.get('human_review_required', True),
            'decision_boundary': metadata.get(
                'decision_boundary',
                'This AI summary supports interviewer review only and must not be treated as a final hiring decision.',
            ),
            'source_excerpt': metadata.get('source_excerpt', ''),
            'limitations': metadata.get('limitations', []),
        }


class InterviewAISummaryUpdateSerializer(ReadableIdModelSerializer):
    class Meta:
        model = InterviewAISummary
        fields = ['strengths', 'weaknesses', 'communication_score', 'overall_impression', 'editable_summary_text']
        extra_kwargs = {
            'strengths': {'required': False},
            'weaknesses': {'required': False},
            'communication_score': {'required': False},
            'overall_impression': {'required': False},
            'editable_summary_text': {'required': False},
        }

    def validate_communication_score(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError('Communication score must be between 0 and 10.')
        return value

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.edited_by = self.context['request'].user
        instance.save(update_fields=[*validated_data.keys(), 'edited_by', 'updated_at'])
        return instance


class EvaluationAnswerInputSerializer(serializers.Serializer):
    criterion_id = serializers.IntegerField()
    score = serializers.DecimalField(max_digits=5, decimal_places=2)
    comment = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)


class EvaluationAnswerSerializer(ReadableIdModelSerializer):
    criterion = EvaluationCriterionSerializer(read_only=True)

    class Meta:
        model = EvaluationAnswer
        fields = ['id', 'criterion', 'score', 'comment']
        read_only_fields = fields


class InterviewEvaluationSerializer(ReadableIdModelSerializer):
    answers = EvaluationAnswerSerializer(many=True, read_only=True)
    interviewer_name = serializers.CharField(source='interviewer.full_name', read_only=True)

    class Meta:
        model = InterviewEvaluation
        fields = ['id', 'interview', 'interviewer', 'interviewer_name', 'total_score', 'overall_comment', 'answers', 'submitted_at']
        read_only_fields = fields


class InterviewEvaluationSubmitSerializer(serializers.Serializer):
    overall_comment = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    answers = EvaluationAnswerInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        interview = self.context['interview']
        form = getattr(interview.application.job, 'interview_evaluation_form', None)
        if not form:
            raise serializers.ValidationError({'answers': 'This job does not have an interview evaluation scorecard configured.'})

        criteria = list(form.criteria.all())
        criteria_by_id = {criterion.id: criterion for criterion in criteria}
        expected_ids = set(criteria_by_id)
        submitted_ids = [answer['criterion_id'] for answer in attrs['answers']]
        submitted_id_set = set(submitted_ids)

        if len(submitted_ids) != len(submitted_id_set):
            raise serializers.ValidationError({'answers': 'Each evaluation criterion can only be answered once.'})
        if submitted_id_set != expected_ids:
            raise serializers.ValidationError({'answers': 'Answers must match all criteria configured for this job evaluation scorecard.'})

        for answer in attrs['answers']:
            criterion = criteria_by_id[answer['criterion_id']]
            score = answer['score']
            if score < 0:
                raise serializers.ValidationError({'answers': f'Score for {criterion.criterion_name} cannot be negative.'})
            if score > criterion.max_score:
                raise serializers.ValidationError({'answers': f'Score for {criterion.criterion_name} cannot exceed {criterion.max_score}.'})
            answer['criterion'] = criterion

        # Keep the submission window open before the scheduled start as well as
        # after it. This intentionally supports pre-interview evaluation
        # submissions used by the current testing/demo workflow, including when
        # transcript and AI-summary deliverables do not exist yet. The deadline
        # is an upper bound only.
        deadline = deliverable_deadline_for(interview)
        if deadline and timezone.now() > deadline:
            raise serializers.ValidationError({
                'deadline': 'Interview deliverables must be submitted no later than 3 days after the scheduled interview datetime.'
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        interview = self.context['interview']
        request = self.context['request']
        answers_data = validated_data.pop('answers')
        total_score = sum((answer['score'] * answer['criterion'].weight_score for answer in answers_data), Decimal('0'))
        total_score = total_score.quantize(Decimal('0.01'))

        evaluation = InterviewEvaluation.objects.create(
            interview=interview,
            interviewer=request.user,
            total_score=total_score,
            overall_comment=validated_data['overall_comment'],
        )
        EvaluationAnswer.objects.bulk_create(
            EvaluationAnswer(
                evaluation=evaluation,
                criterion=answer['criterion'],
                score=answer['score'],
                comment=answer.get('comment', ''),
            )
            for answer in answers_data
        )
        interview.application.change_status(
            JobApplication.Status.UNDER_REVIEW,
            changed_by=request.user,
            note='Interview evaluation submitted.',
        )
        return evaluation


class InterviewEvaluationDetailSerializer(serializers.Serializer):
    interview_id = serializers.IntegerField(source='id')
    application_id = serializers.IntegerField(source='application.id')
    application_status = serializers.CharField(source='application.status')
    job_id = serializers.IntegerField(source='application.job.id')
    job_title = serializers.CharField(source='application.job.title')
    applicant_id = serializers.IntegerField(source='application.applicant.id')
    applicant_name = serializers.CharField(source='application.applicant.full_name')
    transcript = serializers.SerializerMethodField()
    ai_summary = serializers.SerializerMethodField()
    evaluation = serializers.SerializerMethodField()
    evaluations = serializers.SerializerMethodField()

    def get_transcript(self, interview):
        transcript = InterviewTranscript.objects.filter(recording__interview=interview).order_by('-generated_at').first()
        return InterviewTranscriptSerializer(transcript, context=self.context).data if transcript else None

    def get_ai_summary(self, interview):
        summary = InterviewAISummary.objects.filter(transcript__recording__interview=interview).order_by('-updated_at').first()
        return InterviewAISummarySerializer(summary).data if summary else None

    def get_evaluation(self, interview):
        evaluation = self._evaluations_queryset(interview).first()
        return InterviewEvaluationSerializer(evaluation).data if evaluation else None

    def get_evaluations(self, interview):
        return InterviewEvaluationSerializer(self._evaluations_queryset(interview), many=True).data

    def _evaluations_queryset(self, interview):
        return interview.evaluations.select_related('interviewer').prefetch_related('answers__criterion').order_by('-submitted_at')
