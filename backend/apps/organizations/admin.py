from django.contrib import admin

from .models import Organization, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'registration_no', 'email', 'status', 'created_by', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('name', 'registration_no', 'email', 'contact_number', 'created_by__email')


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'user', 'role', 'status', 'joined_at')
    list_filter = ('role', 'status', 'organization')
    search_fields = ('organization__name', 'user__email', 'user__full_name')
