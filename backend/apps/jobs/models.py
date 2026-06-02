from django.db import models

from apps.organizations.models import Organization
from apps.users.models import User


class JobPosting(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='job_postings',
    )
    recruiter = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='recruited_job_postings',
        limit_choices_to={'role': User.Role.RECRUITER},
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    employment_type = models.CharField(max_length=100)
    approximate_salary = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class JobRequirement(models.Model):
    class RequirementType(models.TextChoices):
        SKILL = 'skill', 'Skill'
        EXPERIENCE = 'experience', 'Experience'
        EDUCATION = 'education', 'Education'
        CERTIFICATION = 'certification', 'Certification'
        OTHER = 'other', 'Other'

    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='requirements',
    )
    requirement_type = models.CharField(max_length=20, choices=RequirementType.choices)
    description = models.TextField()
    weight_score = models.DecimalField(max_digits=5, decimal_places=2)
    minimum_threshold = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.job.title} - {self.get_requirement_type_display()}'


class InterviewEvaluationForm(models.Model):
    job = models.OneToOneField(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='interview_evaluation_form',
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class EvaluationCriterion(models.Model):
    form = models.ForeignKey(
        InterviewEvaluationForm,
        on_delete=models.CASCADE,
        related_name='criteria',
    )
    criterion_name = models.CharField(max_length=255)
    description = models.TextField()
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    weight_score = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.criterion_name


class SavedJobPosting(models.Model):
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_job_postings',
        limit_choices_to={'role': User.Role.APPLICANT},
    )
    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='saved_by_applicants',
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['applicant', 'job'],
                name='unique_saved_job_posting',
            ),
        ]

    def __str__(self):
        return f'{self.applicant.email} - {self.job.title}'
