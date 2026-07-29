from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from apps.common.models import ReadableIdModel

from apps.users.models import User


class Organization(ReadableIdModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'
        DELETED = 'deleted', 'Deleted'

    name = models.CharField(max_length=255)
    registration_no = models.CharField(max_length=100)
    email = models.EmailField()
    contact_number = models.CharField(max_length=30)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_organizations',
        limit_choices_to={'role': User.Role.HR_HEAD},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        super().clean()
        if self.created_by_id and self.created_by.role != User.Role.HR_HEAD:
            raise ValidationError({'created_by': 'Only a hiring manager can create an organization.'})

    def __str__(self):
        return self.name


class OrganizationMembership(ReadableIdModel):
    class Role(models.TextChoices):
        HR_HEAD = User.Role.HR_HEAD, 'Hiring Manager'
        RECRUITER = User.Role.RECRUITER, 'Recruiter'
        INTERVIEWER = User.Role.INTERVIEWER, 'Interviewer'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        limit_choices_to={'role__in': Role.values},
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['organization', 'user']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user'],
                name='unique_organization_membership',
            ),
        ]

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != self.role:
            raise ValidationError({'role': "Membership role must match the user's role."})

    def __str__(self):
        return f'{self.user.email} - {self.organization.name} ({self.get_role_display()})'


class OrganizationDeletionOTP(ReadableIdModel):
    """Short-lived, single-use authorization for an organization deletion."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='deletion_otps')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_deletion_otps')
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def set_code(self, code):
        self.code_hash = make_password(code)

    def is_valid_code(self, code):
        return self.used_at is None and self.expires_at > timezone.now() and check_password(code, self.code_hash)
