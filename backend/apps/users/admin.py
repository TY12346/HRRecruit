from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ApplicantProfile, HRHeadProfile, InterviewerProfile, RecruiterProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    ordering = ('id',)
    list_display = ('id', 'email', 'full_name', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'full_name', 'phone_number')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'full_name', 'phone_number', 'role', 'password1', 'password2', 'is_staff', 'is_active'),
            },
        ),
    )


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name')


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name')


@admin.register(InterviewerProfile)
class InterviewerProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name')


@admin.register(HRHeadProfile)
class HRHeadProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name')
