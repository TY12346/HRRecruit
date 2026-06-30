"""Serializers for HR-head organization and team management APIs."""

from django.db import transaction
from rest_framework import serializers

from apps.users.models import User

from .models import Organization, OrganizationMembership
from .services import create_team_member, verify_company_registration


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'registration_no',
            'email',
            'contact_number',
            'address',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def validate_registration_no(self, value):
        if not verify_company_registration(value):
            raise serializers.ValidationError('Company registration could not be verified.')
        return value

    def create(self, validated_data):
        hr_head = self.context['request'].user
        if Organization.objects.filter(created_by=hr_head).exclude(status=Organization.Status.DELETED).exists():
            raise serializers.ValidationError({'detail': 'You already manage an organization.'})

        with transaction.atomic():
            organization = Organization.objects.create(
                created_by=hr_head,
                status=Organization.Status.ACTIVE,
                **validated_data,
            )
            OrganizationMembership.objects.create(
                organization=organization,
                user=hr_head,
                role=OrganizationMembership.Role.HR_HEAD,
            )
        return organization


class OrganizationMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    full_name = serializers.CharField(source='user.full_name')
    phone_number = serializers.CharField(source='user.phone_number', required=False, allow_blank=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ['id', 'user_id', 'email', 'full_name', 'phone_number', 'role', 'status', 'is_active', 'joined_at']
        read_only_fields = ['id', 'status', 'is_active', 'joined_at']

    def validate_role(self, value):
        if value not in (User.Role.RECRUITER, User.Role.INTERVIEWER):
            raise serializers.ValidationError('Only recruiter and interviewer accounts can be created.')
        return value

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = create_team_member(
            organization=self.context['organization'],
            role=validated_data['role'],
            **user_data,
        )
        return user.organization_memberships.get(organization=self.context['organization'])


class OrganizationMemberBulkImportSerializer(serializers.Serializer):
    members = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        max_length=500,
    )

    def validate_members(self, members):
        required_headers = {'email', 'full_name', 'role'}
        for index, row in enumerate(members, start=2):
            normalized_row = {str(key).strip(): value for key, value in row.items()}
            if not required_headers.issubset(normalized_row):
                raise serializers.ValidationError(
                    f'Row {index} must include email, full_name, and role. phone_number is optional.'
                )
        return members

    def save(self):
        created = []
        errors = []
        organization = self.context['organization']
        for row_number, row in enumerate(self.validated_data['members'], start=2):
            member_serializer = OrganizationMemberSerializer(
                data={
                    'email': str(row.get('email', '') or '').strip(),
                    'full_name': str(row.get('full_name', '') or '').strip(),
                    'phone_number': str(row.get('phone_number', '') or '').strip(),
                    'role': str(row.get('role', '') or '').strip().lower(),
                },
                context={'organization': organization},
            )
            if not member_serializer.is_valid():
                errors.append({'row': row_number, 'errors': member_serializer.errors})
                continue
            try:
                membership = member_serializer.save()
            except serializers.ValidationError as error:
                errors.append({'row': row_number, 'errors': error.detail})
                continue
            created.append(OrganizationMemberSerializer(membership).data)

        return {'created': created, 'errors': errors}
