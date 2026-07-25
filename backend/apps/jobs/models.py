from django.db import models

from apps.organizations.models import Organization
from apps.users.models import User


class PositionStatus(models.TextChoices):
    NEW_HEADCOUNT = 'new_headcount', 'New Headcount'
    BACKFILL = 'backfill', 'Backfill'


class JobPosting(models.Model):
    class Status(models.TextChoices):
        DRAFTING = 'drafting', 'Drafting'
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
    approximate_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    salary_range = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255)
    core_responsibilities = models.TextField(blank=True)
    requirements_qualifications = models.TextField(blank=True)
    department = models.CharField(max_length=100, blank=True)
    custom_department = models.CharField(max_length=100, blank=True)
    target_start_date = models.DateField(blank=True, null=True)
    benefits_perks = models.TextField(blank=True)
    position_status = models.CharField(max_length=30, choices=PositionStatus.choices, default=PositionStatus.NEW_HEADCOUNT)
    reason_for_hire = models.TextField(blank=True)
    impact_of_not_hiring = models.TextField(blank=True)
    vacancies = models.PositiveIntegerField(default=1)
    application_deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.DRAFTING)
    requirements_locked_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class JobRequisition(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='job_requisitions')
    recruiter = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_job_requisitions', limit_choices_to={'role': User.Role.RECRUITER})
    title = models.CharField(max_length=255)
    description = models.TextField()
    employment_type = models.CharField(max_length=100)
    approximate_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    salary_range = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255)
    core_responsibilities = models.TextField(blank=True)
    requirements_qualifications = models.TextField(blank=True)
    department = models.CharField(max_length=100, blank=True)
    custom_department = models.CharField(max_length=100, blank=True)
    target_start_date = models.DateField(blank=True, null=True)
    benefits_perks = models.TextField(blank=True)
    position_status = models.CharField(max_length=30, choices=PositionStatus.choices, default=PositionStatus.NEW_HEADCOUNT)
    reason_for_hire = models.TextField(blank=True)
    impact_of_not_hiring = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reviewed_job_requisitions', blank=True, null=True, limit_choices_to={'role': User.Role.HR_HEAD})
    reviewed_at = models.DateTimeField(blank=True, null=True)
    job_posting = models.OneToOneField(JobPosting, on_delete=models.SET_NULL, related_name='source_requisition', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'


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


    class Meta:
        verbose_name = 'Interview evaluation scorecard'
        verbose_name_plural = 'Interview evaluation scorecards'

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
