from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.applications.models import JobApplication
from apps.organizations.models import Organization
from apps.users.models import User


class InterviewerAvailabilitySlot(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        BOOKED = 'booked', 'Booked'
        CANCELLED = 'cancelled', 'Cancelled'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='interviewer_availability_slots',
    )
    interviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='availability_slots',
        limit_choices_to={'role': User.Role.INTERVIEWER},
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_datetime__gt=models.F('start_datetime')),
                name='availability_slot_end_after_start',
            ),
            models.UniqueConstraint(
                fields=['interviewer', 'start_datetime', 'end_datetime'],
                name='unique_interviewer_availability_slot',
            ),
        ]

    def clean(self):
        super().clean()
        if self.interviewer_id and self.interviewer.role != User.Role.INTERVIEWER:
            raise ValidationError({'interviewer': 'Availability slot user must have the interviewer role.'})
        if self.start_datetime and self.end_datetime and self.end_datetime <= self.start_datetime:
            raise ValidationError({'end_datetime': 'Availability slot end time must be after start time.'})

    def __str__(self):
        return f'{self.interviewer} available from {self.start_datetime} to {self.end_datetime}'


class InterviewSchedulingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SCHEDULED = 'scheduled', 'Scheduled'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='interview_scheduling_requests',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='interview_scheduling_requests',
    )
    recruiter = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_interview_scheduling_requests',
        limit_choices_to={'role': User.Role.RECRUITER},
    )
    interviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='interview_scheduling_requests',
        limit_choices_to={'role': User.Role.INTERVIEWER},
    )
    selected_slot = models.OneToOneField(
        InterviewerAvailabilitySlot,
        on_delete=models.SET_NULL,
        related_name='scheduling_request',
        blank=True,
        null=True,
    )
    interview = models.OneToOneField(
        'Interview',
        on_delete=models.SET_NULL,
        related_name='scheduling_request',
        blank=True,
        null=True,
    )
    remark = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if self.recruiter_id and self.recruiter.role != User.Role.RECRUITER:
            raise ValidationError({'recruiter': 'Scheduling request creator must have the recruiter role.'})
        if self.interviewer_id and self.interviewer.role != User.Role.INTERVIEWER:
            raise ValidationError({'interviewer': 'Scheduling request interviewer must have the interviewer role.'})
        if self.application_id and self.organization_id and self.application.job.organization_id != self.organization_id:
            raise ValidationError({'organization': "Scheduling request organization must match the application's job organization."})

    def __str__(self):
        return f'Scheduling request for {self.application}'


class Interview(models.Model):
    class SchedulingMethod(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        SELF_SCHEDULED = 'self_scheduled', 'Self Scheduled'

    class Mode(models.TextChoices):
        ONLINE = 'online', 'Online'
        PHYSICAL = 'physical', 'Physical'
        PHONE = 'phone', 'Phone'

    class Status(models.TextChoices):
        ASSIGNED = 'assigned', 'Assigned'
        INVITATION_SENT = 'invitation_sent', 'Invitation Sent'
        SCHEDULED = 'scheduled', 'Scheduled'
        DECLINED = 'declined', 'Declined'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='interviews',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='interviews',
    )
    recruiter = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_interviews',
        limit_choices_to={'role': User.Role.RECRUITER},
    )
    interviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_interviews',
        blank=True,
        null=True,
        limit_choices_to={'role': User.Role.INTERVIEWER},
    )
    scheduled_datetime = models.DateTimeField(blank=True, null=True)
    availability_slot = models.OneToOneField(
        InterviewerAvailabilitySlot,
        on_delete=models.SET_NULL,
        related_name='interview',
        blank=True,
        null=True,
    )
    scheduling_method = models.CharField(max_length=30, choices=SchedulingMethod.choices, default=SchedulingMethod.MANUAL)
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.ONLINE)
    meeting_link = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ASSIGNED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if self.recruiter_id and self.recruiter.role != User.Role.RECRUITER:
            raise ValidationError({'recruiter': 'Interview recruiter must have the recruiter role.'})
        if self.interviewer_id and self.interviewer.role != User.Role.INTERVIEWER:
            raise ValidationError({'interviewer': 'Interview interviewer must have the interviewer role.'})
        if self.application_id and self.organization_id:
            application_org_id = self.application.job.organization_id
            if application_org_id != self.organization_id:
                raise ValidationError({'organization': "Interview organization must match the application's job organization."})

    def __str__(self):
        return f'Interview for {self.application}'

    @transaction.atomic
    def change_status(self, new_status, changed_by=None, note=''):
        if new_status not in self.Status.values:
            raise ValidationError({'status': f'{new_status!r} is not a valid interview status.'})

        previous_status = self.status
        if previous_status == new_status:
            return None

        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])
        return InterviewStatusHistory.objects.create(
            interview=self,
            from_status=previous_status,
            to_status=new_status,
            changed_by=changed_by,
            note=note,
        )


class InterviewInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        EXPIRED = 'expired', 'Expired'

    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='invitations',
    )
    proposed_datetime = models.DateTimeField()
    mode = models.CharField(max_length=20, choices=Interview.Mode.choices, default=Interview.Mode.ONLINE)
    meeting_link = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    decline_reason = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.interview} invitation - {self.get_status_display()}'


class InterviewStatusHistory(models.Model):
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='status_history',
    )
    from_status = models.CharField(max_length=30, choices=Interview.Status.choices)
    to_status = models.CharField(max_length=30, choices=Interview.Status.choices)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='interview_status_changes',
        blank=True,
        null=True,
    )
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Interview status history'
        verbose_name_plural = 'Interview status histories'

    def __str__(self):
        return f'{self.interview} - {self.from_status} to {self.to_status}'


class CalendarEvent(models.Model):
    class SyncStatus(models.TextChoices):
        NOT_SYNCED = 'not_synced', 'Not Synced'
        SYNCED = 'synced', 'Synced'
        FAILED = 'failed', 'Failed'

    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='calendar_events',
    )
    provider = models.CharField(max_length=100, default='local')
    external_event_id = models.CharField(max_length=255, blank=True)
    calendar_link = models.URLField(max_length=1000, blank=True)
    last_synced_at = models.DateTimeField(blank=True, null=True)
    sync_status = models.CharField(max_length=20, choices=SyncStatus.choices, default=SyncStatus.NOT_SYNCED)

    class Meta:
        ordering = ['interview', 'provider']

    def __str__(self):
        return f'{self.provider} calendar event for {self.interview}'
