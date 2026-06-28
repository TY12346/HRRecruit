from django.core.exceptions import ValidationError
from django.db import models

from apps.applications.models import JobApplication
from apps.users.models import User


class HiringDecision(models.Model):
    class Decision(models.TextChoices):
        HIRE = 'hire', 'Hire'
        REJECT = 'reject', 'Reject'

    class Status(models.TextChoices):
        PENDING_HR_APPROVAL = 'pending_hr_approval', 'Pending HR Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='hiring_decisions',
    )
    recruiter = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='submitted_hiring_decisions',
        limit_choices_to={'role': User.Role.RECRUITER},
    )
    decision = models.CharField(max_length=10, choices=Decision.choices)
    recruiter_justification = models.TextField()
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_HR_APPROVAL,
    )
    hr_head = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='reviewed_hiring_decisions',
        blank=True,
        null=True,
        limit_choices_to={'role': User.Role.HR_HEAD},
    )
    hr_head_justification = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-submitted_at']

    def clean(self):
        super().clean()
        if self.recruiter_id and self.recruiter.role != User.Role.RECRUITER:
            raise ValidationError({'recruiter': 'Hiring decision recruiter must have the recruiter role.'})
        if self.hr_head_id and self.hr_head.role != User.Role.HR_HEAD:
            raise ValidationError({'hr_head': 'Hiring decision reviewer must have the HR head role.'})

    def __str__(self):
        return f'{self.application} - {self.get_decision_display()}'


class JobOffer(models.Model):
    class OfferStatus(models.TextChoices):
        SENT = 'sent', 'Sent'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        EXPIRED = 'expired', 'Expired'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='job_offers',
    )
    offer_letter_file = models.FileField(upload_to='offer_letters/', blank=True, null=True)
    offer_message = models.TextField()
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_currency = models.CharField(max_length=3, default='MYR')
    start_date = models.DateField(blank=True, null=True)
    employment_type = models.CharField(max_length=100, blank=True)
    work_arrangement = models.CharField(max_length=50, blank=True)
    probation_months = models.PositiveSmallIntegerField(blank=True, null=True)
    benefits_summary = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    candidate_response_note = models.TextField(blank=True)
    offer_status = models.CharField(max_length=20, choices=OfferStatus.choices, default=OfferStatus.SENT)
    respond_deadline = models.DateTimeField()
    sent_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    withdrawn_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.application} offer - {self.get_offer_status_display()}'
