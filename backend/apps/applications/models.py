from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q

from apps.jobs.models import JobPosting
from apps.users.models import ApplicantResume, User


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        REJECTED = 'rejected', 'Rejected'

    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications',
        limit_choices_to={'role': User.Role.APPLICANT},
    )
    resume = models.ForeignKey(
        ApplicantResume,
        on_delete=models.SET_NULL,
        related_name='applications',
        blank=True,
        null=True,
    )
    application_resume = models.FileField(
        upload_to='application_resumes/',
        blank=True,
        null=True,
    )
    application_resume_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.APPLIED)
    recruiter_remark = models.TextField(blank=True)
    assigned_interviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_job_applications',
        blank=True,
        null=True,
        limit_choices_to={'role': User.Role.INTERVIEWER},
    )
    extracted_resume_text = models.TextField(blank=True)
    extracted_skills = models.JSONField(default=list, blank=True)
    extracted_experience = models.JSONField(default=dict, blank=True)
    extracted_education = models.JSONField(default=dict, blank=True)
    semantic_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    skill_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    experience_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    education_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    score_explanation = models.JSONField(default=dict, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['applicant', 'job'],
                condition=~Q(status='rejected'),
                name='unique_job_application',
            ),
        ]

    def __str__(self):
        return f'{self.applicant.email} - {self.job.title}'

    @transaction.atomic
    def change_status(self, new_status, changed_by=None, note=''):
        if new_status not in self.Status.values:
            raise ValidationError({'status': f'{new_status!r} is not a valid application status.'})

        previous_status = self.status
        if previous_status == new_status:
            return None

        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])
        return ApplicationStageHistory.objects.create(
            application=self,
            from_stage=previous_status,
            to_stage=new_status,
            changed_by=changed_by,
            note=note,
        )


class ApplicationStageHistory(models.Model):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='stage_history',
    )
    from_stage = models.CharField(max_length=30, choices=JobApplication.Status.choices)
    to_stage = models.CharField(max_length=30, choices=JobApplication.Status.choices)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='application_stage_changes',
        blank=True,
        null=True,
    )
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Application stage history'
        verbose_name_plural = 'Application stage histories'

    def __str__(self):
        return f'{self.application} - {self.from_stage} to {self.to_stage}'

class EmployerInvite(models.Model):
    class Response(models.TextChoices):
        NO_RESPONSE = 'no_response', 'No response'
        APPLIED = 'applied', 'Applied for job'
        DECLINED = 'declined', 'Declined'

    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='employer_invites')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employer_invites', limit_choices_to={'role': User.Role.APPLICANT})
    recruiter = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sent_employer_invites', limit_choices_to={'role': User.Role.RECRUITER})
    response = models.CharField(max_length=20, choices=Response.choices, default=Response.NO_RESPONSE)
    responded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['job', 'applicant'], name='unique_employer_invite_per_job_applicant')]

    def __str__(self):
        return f'{self.job.title} invite for {self.applicant.email}'
