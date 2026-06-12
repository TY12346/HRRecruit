"""HR-head organization and team setup API views."""

from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsHRHead

from .models import Organization, OrganizationMembership
from .services import delete_organization_account, get_organization_deletion_blockers
from .serializers import (
    OrganizationMemberBulkImportSerializer,
    OrganizationMemberSerializer,
    OrganizationSerializer,
)


def get_managed_organization(hr_head):
    """Return the HR head's non-deleted organization, if one exists."""
    return Organization.objects.filter(created_by=hr_head).exclude(status=Organization.Status.DELETED).first()


class ManagedOrganizationMixin:
    permission_classes = [IsHRHead]

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
    def post(self, request):
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()
        serializer = OrganizationMemberSerializer(data=request.data, context={'organization': organization})
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            {'message': 'Team member created successfully.', 'member': OrganizationMemberSerializer(membership).data},
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        organization = self.get_organization(request)
        if not organization:
            return self.organization_not_found_response()
        memberships = organization.memberships.exclude(role=OrganizationMembership.Role.HR_HEAD).select_related('user')
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
        membership = organization.memberships.exclude(role=OrganizationMembership.Role.HR_HEAD).filter(id=member_id).select_related('user').first()
        if not membership:
            return Response({'detail': 'Team member not found.'}, status=status.HTTP_404_NOT_FOUND)

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
            {'message': 'CSV import completed.', **result},
            status=status.HTTP_201_CREATED,
        )
