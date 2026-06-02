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


class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    organization_name = serializers.CharField(source='job.organization.name', read_only=True)
    applicant = ApplicationApplicantSerializer(read_only=True)

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


class ApplicationStageHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model = ApplicationStageHistory
        fields = ['id', 'from_stage', 'to_stage', 'changed_by', 'changed_by_name', 'note', 'changed_at']
        read_only_fields = fields
