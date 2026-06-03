from rest_framework import serializers

from apps.applications.serializers import JobApplicationSerializer
from .models import HiringDecision, JobOffer


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


class JobOfferCreateSerializer(serializers.Serializer):
    offer_message = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    respond_deadline = serializers.DateTimeField(required=True)
    offer_letter_file = serializers.FileField(required=False, allow_empty_file=False)

    def validate_offer_letter_file(self, value):
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('Offer letter file must not exceed 5 MB.')
        allowed_extensions = ('.pdf', '.doc', '.docx')
        if not value.name.lower().endswith(allowed_extensions):
            raise serializers.ValidationError('Offer letter file must be a PDF, DOC, or DOCX file.')
        return value


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
            'respond_deadline',
            'sent_at',
            'responded_at',
        ]
        read_only_fields = fields

    def get_offer_letter_url(self, offer):
        if not offer.offer_letter_file:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(offer.offer_letter_file.url)
        return offer.offer_letter_file.url
