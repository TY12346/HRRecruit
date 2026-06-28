from django.utils import timezone
from rest_framework import serializers

from apps.applications.serializers import JobApplicationSerializer
from apps.users.models import User
from .models import HiringDecision, JobOffer


ALLOWED_OFFER_LETTER_CONTENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}


class HiringDecisionSubmitSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=HiringDecision.Decision.choices)
    justification = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)


class HRDecisionReviewSerializer(serializers.Serializer):
    justification = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)


class HiringDecisionSerializer(serializers.ModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    recruiter_name = serializers.CharField(source='recruiter.full_name', read_only=True)
    recruiter_email = serializers.EmailField(source='recruiter.email', read_only=True)
    hr_head_name = serializers.CharField(source='hr_head.full_name', read_only=True)
    hr_head_email = serializers.EmailField(source='hr_head.email', read_only=True)

    class Meta:
        model = HiringDecision
        fields = [
            'id',
            'application',
            'recruiter',
            'recruiter_name',
            'recruiter_email',
            'decision',
            'recruiter_justification',
            'status',
            'hr_head',
            'hr_head_name',
            'hr_head_email',
            'hr_head_justification',
            'submitted_at',
            'reviewed_at',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == User.Role.APPLICANT:
            for field in (
                'recruiter',
                'recruiter_name',
                'recruiter_email',
                'recruiter_justification',
                'hr_head',
                'hr_head_name',
                'hr_head_email',
                'hr_head_justification',
            ):
                data.pop(field, None)
        return data


class JobOfferCreateSerializer(serializers.Serializer):
    offer_message = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    respond_deadline = serializers.DateTimeField(required=True)
    offer_letter_file = serializers.FileField(required=False, allow_empty_file=False)
    salary_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    salary_currency = serializers.CharField(required=False, allow_blank=False, max_length=3)
    start_date = serializers.DateField(required=False, allow_null=True)
    employment_type = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    work_arrangement = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    probation_months = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=60)
    benefits_summary = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate_respond_deadline(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError('Response deadline must be in the future.')
        return value

    def validate_salary_currency(self, value):
        return value.upper()

    def validate_offer_letter_file(self, value):
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('Offer letter file must not exceed 5 MB.')
        allowed_extensions = ('.pdf', '.doc', '.docx')
        if not value.name.lower().endswith(allowed_extensions):
            raise serializers.ValidationError('Offer letter file must be a PDF, DOC, or DOCX file.')
        content_type = getattr(value, 'content_type', '')
        if content_type and content_type not in ALLOWED_OFFER_LETTER_CONTENT_TYPES:
            raise serializers.ValidationError('Unsupported offer letter content type.')
        return value


class JobOfferAcceptSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)


class JobOfferDeclineSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)


class JobOfferSerializer(serializers.ModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    offer_letter_url = serializers.SerializerMethodField()

    class Meta:
        model = JobOffer
        fields = [
            'id',
            'application',
            'offer_letter_file',
            'offer_letter_url',
            'offer_message',
            'offer_status',
            'salary_amount',
            'salary_currency',
            'start_date',
            'employment_type',
            'work_arrangement',
            'probation_months',
            'benefits_summary',
            'internal_notes',
            'candidate_response_note',
            'respond_deadline',
            'sent_at',
            'responded_at',
            'withdrawn_at',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == User.Role.APPLICANT:
            data.pop('internal_notes', None)
        return data

    def get_offer_letter_url(self, offer):
        if not offer.offer_letter_file:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(offer.offer_letter_file.url)
        return offer.offer_letter_file.url
