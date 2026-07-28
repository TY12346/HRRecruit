"""hiring manager organization and team setup API views."""

from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.email_service import email_delivery_mode
from apps.users.models import User
from apps.users.permissions import IsHiringManager, IsRecruiterOrHiringManager

from .models import Organization, OrganizationMembership
from .services import delete_organization_account, get_organization_deletion_blockers
from .serializers import (
    OrganizationMemberBulkImportSerializer,
    OrganizationMemberSerializer,
    OrganizationSerializer,
)


def get_active_membership_organization(user, role):
    membership = OrganizationMembership.objects.filter(
        user=user,
        role=role,
        status=OrganizationMembership.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    ).select_related('organization').first()
    return membership.organization if membership else None


def get_managed_organization(hr_head):
    """Return the hiring manager's non-deleted organization, if one exists."""
    return get_active_membership_organization(hr_head, OrganizationMembership.Role.HR_HEAD)


class ManagedOrganizationMixin:
    permission_classes = [IsHiringManager]

    def get_organization(self, request):
        return get_managed_organization(request.user)

    def organization_not_found_response(self):
        return Response({'detail': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)


class OrganizationCreateAPIView(ManagedOrganizationMixin, APIView):
    def post(self, request):
        serializer = OrganizationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        return Response(
            {'message': 'Organization created successfully.', 'organization': OrganizationSerializer(organization).data},
            status=status.HTTP_201_CREATED,
        )


class OrganizationAPIView(ManagedOrganizationMixin, APIView):
    def get(self, request):
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()
        return Response(OrganizationSerializer(organization).data)

    def patch(self, request):
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Organization updated successfully.', 'organization': serializer.data})

    def delete(self, request):
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()

        blockers = get_organization_deletion_blockers(organization)
        if blockers:
            return Response(
                {'detail': 'Organization cannot be deleted yet.', 'blockers': blockers},
                status=status.HTTP_409_CONFLICT,
            )

        delete_organization_account(organization)
        return Response({'message': 'Organization account deleted successfully.'})


class OrganizationMemberListCreateAPIView(ManagedOrganizationMixin, APIView):
    permission_classes = [IsRecruiterOrHiringManager]

    def get_organization(self, request):
        if request.user.role == User.Role.HR_HEAD:
            return get_managed_organization(request.user)
        if request.user.role == User.Role.RECRUITER:
            return get_active_membership_organization(request.user, OrganizationMembership.Role.RECRUITER)
        return None

    def post(self, request):
        if request.user.role != User.Role.HR_HEAD:
            return Response({'detail': 'Only hiring managers can create organization team members.'}, status=status.HTTP_403_FORBIDDEN)
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()
        serializer = OrganizationMemberSerializer(data=request.data, context={'organization': organization})
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        delivery_mode = email_delivery_mode()
        if delivery_mode == 'console':
            message = (
                'Team member created successfully. The temporary credentials were printed in the backend console '
                'because SMTP email delivery is not configured.'
            )
        elif delivery_mode == 'development':
            message = 'Team member created successfully. The configured development email backend captured the temporary credentials.'
        else:
            message = 'Team member created successfully. Temporary credentials were sent by email.'
        return Response(
            {
                'message': message,
                'email_delivery': delivery_mode,
                'member': OrganizationMemberSerializer(membership).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()
        memberships = organization.memberships.select_related('user', 'organization')
        search = request.query_params.get('search', '').strip()
        if search:
            memberships = memberships.filter(
                Q(user__full_name__icontains=search)
                | Q(user__email__icontains=search)
                | Q(role__icontains=search)
            )
        return Response(OrganizationMemberSerializer(memberships, many=True).data)


class OrganizationMemberDeactivateAPIView(ManagedOrganizationMixin, APIView):
    @transaction.atomic
    def patch(self, request, member_id):
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()
        membership = organization.memberships.filter(id=member_id).select_related('user').first()
        if not membership:
            return Response({'detail': 'Team member not found.'}, status=status.HTTP_404_NOT_FOUND)
        if membership.user_id == request.user.id:
            return Response({'detail': 'You cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)
        if membership.user_id == organization.created_by_id:
            return Response({'detail': 'The original organization owner cannot be deactivated.'}, status=status.HTTP_400_BAD_REQUEST)
        if membership.role == OrganizationMembership.Role.HR_HEAD and organization.memberships.filter(
            role=OrganizationMembership.Role.HR_HEAD,
            status=OrganizationMembership.Status.ACTIVE,
            user__is_active=True,
        ).count() <= 1:
            return Response(
                {'detail': 'The organization must retain at least one active Hiring Manager.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.status = OrganizationMembership.Status.INACTIVE
        membership.save(update_fields=['status'])
        membership.user.is_active = False
        membership.user.save(update_fields=['is_active'])
        return Response({'message': 'Team member deactivated successfully.', 'member': OrganizationMemberSerializer(membership).data})


class OrganizationMemberBulkImportAPIView(ManagedOrganizationMixin, APIView):
    def post(self, request):
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()
        serializer = OrganizationMemberBulkImportSerializer(
            data=request.data,
            context={'organization': organization},
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(
            {'message': 'Spreadsheet import completed.', **result},
            status=status.HTTP_201_CREATED,
        )
