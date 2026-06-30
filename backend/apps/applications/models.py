from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.jobs.models import JobPosting
from apps.users.models import ApplicantResume, User


class JobApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        SCREENED = 'screened', 'Screened'
        SCREENED_QUALIFIED = 'screened_qualified', 'Screened Qualified'
        SCREENED_NOT_QUALIFIED = 'screened_not_qualified', 'Screened Not Qualified'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        REJECTED = 'rejected', 'Rejected'
        INTERVIEW_INVITED = 'interview_invited', 'Interview Invited'
        INTERVIEW_ACCEPTED = 'interview_accepted', 'Interview Accepted'
        INTERVIEW_DECLINED = 'interview_declined', 'Interview Declined'
        INTERVIEWING = 'interviewing', 'Interviewing'
        EVALUATION_SUBMITTED = 'evaluation_submitted', 'Evaluation Submitted'
        DECISION_PENDING = 'decision_pending', 'Decision Pending'
        HR_APPROVED = 'hr_approved', 'HR Approved'
        HR_REJECTED = 'hr_rejected', 'HR Rejected'
        OFFER_SENT = 'offer_sent', 'Offer Sent'
        OFFER_ACCEPTED = 'offer_accepted', 'Offer Accepted'
        OFFER_DECLINED = 'offer_declined', 'Offer Declined'
        HIRED = 'hired', 'Hired'

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
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.SUBMITTED)
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
