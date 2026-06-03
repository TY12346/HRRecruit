"""Serializers for role-protected job application APIs."""

from rest_framework import serializers

from .models import ApplicationStageHistory, JobApplication


class ApplicationApplicantSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    linkedin_url = serializers.CharField(source='applicant_profile.linkedin_url', read_only=True)
    personal_summary = serializers.CharField(source='applicant_profile.personal_summary', read_only=True)
    resume_file = serializers.FileField(source='applicant_profile.resume_file', read_only=True)


class AssignedInterviewerSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)


class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    organization_name = serializers.CharField(source='job.organization.name', read_only=True)
    applicant = ApplicationApplicantSerializer(read_only=True)
    assigned_interviewer = AssignedInterviewerSerializer(read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            'id',
            'job',
            'job_title',
            'organization_name',
            'applicant',
            'status',
            'recruiter_remark',
            'assigned_interviewer',
            'extracted_resume_text',
            'extracted_skills',
            'extracted_experience',
            'extracted_education',
            'semantic_score',
            'skill_score',
            'experience_score',
            'education_score',
            'final_score',
            'score_explanation',
            'applied_at',
            'updated_at',
        ]
        read_only_fields = fields


class CandidateScoreSerializer(serializers.Serializer):
    semantic_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    skill_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    experience_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    education_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    final_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    explanation = serializers.JSONField(source='score_explanation', read_only=True)


class CandidateProfileSerializer(serializers.ModelSerializer):
    applicant_profile = ApplicationApplicantSerializer(source='applicant', read_only=True)
    resume_info = serializers.SerializerMethodField()
    scores = CandidateScoreSerializer(source='*', read_only=True)
    assigned_interviewer = AssignedInterviewerSerializer(read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            'id',
            'job',
            'applicant_profile',
            'resume_info',
            'extracted_skills',
            'scores',
            'status',
            'recruiter_remark',
            'assigned_interviewer',
            'applied_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_resume_info(self, application):
        applicant_profile = getattr(application.applicant, 'applicant_profile', None)
        resume_file = getattr(applicant_profile, 'resume_file', None)
        resume_url = None
        if resume_file:
            request = self.context.get('request')
            if request:
                resume_url = request.build_absolute_uri(resume_file.url)
            else:
                resume_url = resume_file.url
        return {
            'resume_file': resume_file.name if resume_file else '',
            'resume_url': resume_url,
            'extracted_resume_text': application.extracted_resume_text,
            'extracted_experience': application.extracted_experience,
            'extracted_education': application.extracted_education,
        }


class ApplicationShortlistSerializer(serializers.Serializer):
    interviewer_id = serializers.IntegerField(required=True)
    remark = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)


class ApplicationRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    remark = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate(self, attrs):
        if not attrs.get('reason') and not attrs.get('remark'):
            raise serializers.ValidationError({'reason': 'Rejecting a candidate requires a reason or remark.'})
        return attrs


class ApplicationRemarkSerializer(serializers.Serializer):
    remark = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)


class ApplicationStageHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model = ApplicationStageHistory
        fields = ['id', 'from_stage', 'to_stage', 'changed_by', 'changed_by_name', 'note', 'changed_at']
        read_only_fields = fields
