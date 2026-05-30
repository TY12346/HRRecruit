from django.urls import path

from .views import (
    OrganizationAPIView,
    OrganizationCreateAPIView,
    OrganizationMemberBulkImportAPIView,
    OrganizationMemberDeactivateAPIView,
    OrganizationMemberListCreateAPIView,
)

urlpatterns = [
    path('create/', OrganizationCreateAPIView.as_view(), name='organization-create'),
    path('', OrganizationAPIView.as_view(), name='organization-detail'),
    path('members/', OrganizationMemberListCreateAPIView.as_view(), name='organization-member-list-create'),
    path('members/bulk/', OrganizationMemberBulkImportAPIView.as_view(), name='organization-member-bulk-import'),
    path('members/<int:member_id>/deactivate/', OrganizationMemberDeactivateAPIView.as_view(), name='organization-member-deactivate'),
]
