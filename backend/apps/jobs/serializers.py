"""Serializers for job posting, requirement, evaluation form, and saved-job APIs."""

from decimal import Decimal, ROUND_DOWN

from django.db import transaction
from rest_framework import serializers

from .models import EvaluationCriterion, InterviewEvaluationForm, JobPosting, JobRequirement


class JobRequirementSerializer(serializers.ModelSerializer):
    def validate_weight_score(self, value):
        if value < 0:
            raise serializers.ValidationError('Weight score cannot be negative.')
        return value

    class Meta:
        model = JobRequirement
        fields = ['id', 'requirement_type', 'description', 'weight_score', 'minimum_threshold', 'created_at']
        read_only_fields = ['id', 'created_at']


class EvaluationCriterionSerializer(serializers.ModelSerializer):
    def validate_weight_score(self, value):
        if value < 0:
            raise serializers.ValidationError('Weight score cannot be negative.')
        return value

    class Meta:
        model = EvaluationCriterion
        fields = ['id', 'criterion_name', 'description', 'max_score', 'weight_score', 'created_at']
        read_only_fields = ['id', 'created_at']


class InterviewEvaluationFormSerializer(serializers.ModelSerializer):
    criteria = EvaluationCriterionSerializer(many=True)

    class Meta:
        model = InterviewEvaluationForm
        fields = ['id', 'title', 'criteria', 'created_at']
        read_only_fields = ['id', 'created_at']

    @transaction.atomic
    def create(self, validated_data):
        criteria = validated_data.pop('criteria')
        form = InterviewEvaluationForm.objects.create(**validated_data)
        EvaluationCriterion.objects.bulk_create(
            EvaluationCriterion(form=form, **criterion) for criterion in criteria
        )
        return form


class JobPostingSerializer(serializers.ModelSerializer):
    requirements = JobRequirementSerializer(many=True, read_only=True)
    interview_evaluation_form = InterviewEvaluationFormSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    recruiter_name = serializers.CharField(source='recruiter.full_name', read_only=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = [
            'id',
            'organization',
            'organization_name',
            'recruiter',
            'recruiter_name',
            'title',
            'description',
            'employment_type',
            'approximate_salary',
            'location',
            'status',
            'requirements',
            'interview_evaluation_form',
            'is_saved',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'organization',
            'organization_name',
            'recruiter',
            'recruiter_name',
            'requirements',
            'interview_evaluation_form',
            'is_saved',
            'created_at',
            'updated_at',
        ]

    def get_is_saved(self, job):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user.role != 'applicant':
            return False
        return job.saved_by_applicants.filter(applicant=request.user).exists()


class JobRequirementConfigurationSerializer(serializers.Serializer):
    requirements = JobRequirementSerializer(many=True, allow_empty=False)
    normalize_weights = serializers.BooleanField(default=False, write_only=True)

    def validate(self, attrs):
        requirements = attrs['requirements']
        total = sum((requirement['weight_score'] for requirement in requirements), Decimal('0'))
        if total <= 0:
            raise serializers.ValidationError({'requirements': 'Requirement weights must sum to 1.0.'})
        if total != Decimal('1.0'):
            if not attrs['normalize_weights']:
                raise serializers.ValidationError(
                    {'requirements': 'Requirement weights must sum to 1.0. Set normalize_weights=true to normalize them.'}
                )
            self._normalize(requirements, total)
        return attrs

    @staticmethod
    def _normalize(requirements, total):
        """Normalize two-decimal model weights while keeping their sum exactly 1.00."""
        remaining = Decimal('1.00')
        for requirement in requirements[:-1]:
            weight = (requirement['weight_score'] / total).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            requirement['weight_score'] = weight
            remaining -= weight
        requirements[-1]['weight_score'] = remaining

    @transaction.atomic
    def create(self, validated_data):
        job = self.context['job']
        requirements = validated_data['requirements']
        job.requirements.all().delete()
        return JobRequirement.objects.bulk_create(
            JobRequirement(job=job, **requirement) for requirement in requirements
        )
