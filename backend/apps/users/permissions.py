"""Reusable role-based permissions for HRRecruit API views."""

from rest_framework.permissions import BasePermission

from .models import User


class RolePermission(BasePermission):
    """Allow authenticated users whose role is listed in ``allowed_roles``."""

    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in self.allowed_roles
        )


class IsApplicant(RolePermission):
    """Allow authenticated job applicants only."""

    allowed_roles = (User.Role.APPLICANT,)


class IsRecruiter(RolePermission):
    """Allow authenticated recruiters only."""

    allowed_roles = (User.Role.RECRUITER,)


class IsInterviewer(RolePermission):
    """Allow authenticated interviewers only."""

    allowed_roles = (User.Role.INTERVIEWER,)


class IsHRHead(RolePermission):
    """Allow authenticated HR department heads only."""

    allowed_roles = (User.Role.HR_HEAD,)


class IsRecruiterOrHRHead(RolePermission):
    """Allow authenticated recruiters and HR department heads only."""

    allowed_roles = (User.Role.RECRUITER, User.Role.HR_HEAD)


class IsOrganizationMember(RolePermission):
    """Allow roles that belong to an organization.

    This permission provides a reusable organization-member role gate. Object-
    level organization isolation should be added after the Organization model
    and its user relationship exist.
    """

    allowed_roles = (
        User.Role.RECRUITER,
        User.Role.INTERVIEWER,
        User.Role.HR_HEAD,
    )
