"""Serializers for HR-head organization and team management APIs."""

import csv
import io

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


ALLOWED_CSV_CONTENT_TYPES = {'text/csv', 'application/csv', 'application/vnd.ms-excel'}


class OrganizationMemberBulkImportSerializer(serializers.Serializer):
    csv_file = serializers.FileField()

    def validate_csv_file(self, csv_file):
        if not csv_file.name.lower().endswith('.csv'):
            raise serializers.ValidationError('Only CSV files are supported. Excel import can be added later.')
        if csv_file.size > 1024 * 1024:
            raise serializers.ValidationError('CSV file must not exceed 1MB.')
        content_type = getattr(csv_file, 'content_type', '')
        if content_type and content_type not in ALLOWED_CSV_CONTENT_TYPES:
            raise serializers.ValidationError('Unsupported CSV content type.')
        return csv_file

    def save(self):
        csv_file = self.validated_data['csv_file']
        try:
            content = csv_file.read().decode('utf-8-sig')
        except UnicodeDecodeError as error:
            raise serializers.ValidationError({'csv_file': 'CSV file must be UTF-8 encoded.'}) from error

        reader = csv.DictReader(io.StringIO(content))
        required_headers = {'email', 'full_name', 'role'}
        if not reader.fieldnames or not required_headers.issubset(set(reader.fieldnames)):
            raise serializers.ValidationError(
                {'csv_file': 'CSV headers must include email, full_name, and role. phone_number is optional.'}
            )

        created = []
        errors = []
        organization = self.context['organization']
        for row_number, row in enumerate(reader, start=2):
            member_serializer = OrganizationMemberSerializer(
                data={
                    'email': row.get('email', '').strip(),
                    'full_name': row.get('full_name', '').strip(),
                    'phone_number': row.get('phone_number', '').strip(),
                    'role': row.get('role', '').strip(),
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
