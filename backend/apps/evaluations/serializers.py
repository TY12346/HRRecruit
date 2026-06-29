"""Serializers for interview recordings, transcripts, summaries, and evaluations."""

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.applications.models import JobApplication
from apps.jobs.serializers import EvaluationCriterionSerializer
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


class InterviewRecordingSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)

    class Meta:
        model = InterviewRecording
        fields = ['id', 'interview', 'audio_file', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['id', 'interview', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']


class InterviewRecordingUploadSerializer(serializers.ModelSerializer):
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
        return InterviewRecording.objects.create(
            interview=self.context['interview'],
            uploaded_by=self.context['request'].user,
            **validated_data,
        )


class InterviewTranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewTranscript
        fields = ['id', 'recording', 'transcript_text', 'transcript_json', 'generated_at']
        read_only_fields = fields


class InterviewAISummarySerializer(serializers.ModelSerializer):
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


class InterviewAISummaryUpdateSerializer(serializers.ModelSerializer):
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


class EvaluationAnswerSerializer(serializers.ModelSerializer):
    criterion = EvaluationCriterionSerializer(read_only=True)

    class Meta:
        model = EvaluationAnswer
        fields = ['id', 'criterion', 'score', 'comment']
        read_only_fields = fields


class InterviewEvaluationSerializer(serializers.ModelSerializer):
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
            raise serializers.ValidationError({'answers': 'This job does not have an interview evaluation form configured.'})

        criteria = list(form.criteria.all())
        criteria_by_id = {criterion.id: criterion for criterion in criteria}
        expected_ids = set(criteria_by_id)
        submitted_ids = [answer['criterion_id'] for answer in attrs['answers']]
        submitted_id_set = set(submitted_ids)

        if len(submitted_ids) != len(submitted_id_set):
            raise serializers.ValidationError({'answers': 'Each evaluation criterion can only be answered once.'})
        if submitted_id_set != expected_ids:
            raise serializers.ValidationError({'answers': 'Answers must match all criteria configured for this job evaluation form.'})

        for answer in attrs['answers']:
            criterion = criteria_by_id[answer['criterion_id']]
            score = answer['score']
            if score < 0:
                raise serializers.ValidationError({'answers': f'Score for {criterion.criterion_name} cannot be negative.'})
            if score > criterion.max_score:
                raise serializers.ValidationError({'answers': f'Score for {criterion.criterion_name} cannot exceed {criterion.max_score}.'})
            answer['criterion'] = criterion

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
            JobApplication.Status.EVALUATION_SUBMITTED,
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

    def get_transcript(self, interview):
        transcript = InterviewTranscript.objects.filter(recording__interview=interview).order_by('-generated_at').first()
        return InterviewTranscriptSerializer(transcript).data if transcript else None

    def get_ai_summary(self, interview):
        summary = InterviewAISummary.objects.filter(transcript__recording__interview=interview).order_by('-updated_at').first()
        return InterviewAISummarySerializer(summary).data if summary else None

    def get_evaluation(self, interview):
        evaluation = interview.evaluations.prefetch_related('answers__criterion').order_by('-submitted_at').first()
        return InterviewEvaluationSerializer(evaluation).data if evaluation else None
