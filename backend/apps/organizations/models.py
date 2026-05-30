from django.core.exceptions import ValidationError
from django.db import models

from apps.users.models import User


class Organization(models.Model):
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
            raise ValidationError({'created_by': 'Only an HR head can create an organization.'})

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        HR_HEAD = User.Role.HR_HEAD, 'HR Head'
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
