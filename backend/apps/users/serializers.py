import random

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.email_service import (
    build_password_reset_link,
    is_development_email_backend,
    send_password_reset_otp_email,
)

from .models import ApplicantProfile, PasswordResetOTP, User, create_profile_for_user


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'password']

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if User.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            role=User.Role.HR_HEAD,
            **validated_data,
        )
        return user


class ApplicantRegisterSerializer(RegisterSerializer):
    def validate(self, attrs):
        existing_user = User.objects.filter(email__iexact=attrs['email']).first()
        if existing_user:
            can_convert = (
                existing_user.role != User.Role.APPLICANT
                and existing_user.check_password(attrs['password'])
                and not existing_user.created_organizations.exists()
                and not existing_user.organization_memberships.exists()
            )
            if not can_convert:
                raise serializers.ValidationError({'email': 'A user with this email already exists.'})
            attrs['_convert_user'] = existing_user
        return attrs

    def create(self, validated_data):
        user_to_convert = validated_data.pop('_convert_user', None)
        password = validated_data.pop('password')
        if user_to_convert:
            user_to_convert.full_name = validated_data['full_name']
            user_to_convert.phone_number = validated_data.get('phone_number', '')
            user_to_convert.role = User.Role.APPLICANT
            user_to_convert.set_password(password)
            user_to_convert.save(update_fields=['full_name', 'phone_number', 'role', 'password'])
            if hasattr(user_to_convert, 'hr_head_profile'):
                user_to_convert.hr_head_profile.delete()
            create_profile_for_user(user_to_convert)
            return user_to_convert

        return User.objects.create_user(
            password=password,
            role=User.Role.APPLICANT,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['email'], password=attrs['password'])
        if not user or not user.is_active:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    linkedin_url = serializers.URLField(source='applicant_profile.linkedin_url', required=False, allow_blank=True)
    personal_summary = serializers.CharField(source='applicant_profile.personal_summary', required=False, allow_blank=True)
    resume_file = serializers.FileField(source='applicant_profile.resume_file', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'role', 'linkedin_url', 'personal_summary', 'resume_file']
        read_only_fields = ['id', 'email', 'role', 'resume_file']

    def update(self, instance, validated_data):
        applicant_data = validated_data.pop('applicant_profile', {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=list(validated_data.keys()) if validated_data else None)

        if instance.role == User.Role.APPLICANT and applicant_data:
            profile = instance.applicant_profile
            for attr, value in applicant_data.items():
                setattr(profile, attr, value)
            profile.save(update_fields=list(applicant_data.keys()))
        return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    CLIENT_WEB = 'web'
    CLIENT_MOBILE = 'mobile'
    STAFF_ROLES = {User.Role.HR_HEAD, User.Role.RECRUITER, User.Role.INTERVIEWER}

    email = serializers.EmailField()
    client_app = serializers.ChoiceField(choices=(CLIENT_WEB, CLIENT_MOBILE))

    def save(self):
        email = self.validated_data['email']
        user = User.objects.filter(email__iexact=email).first()
        if not user or not _user_can_reset_from_client(user, self.validated_data['client_app']):
            return {}

        otp_code = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        PasswordResetOTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at)

        delivery = send_password_reset_otp_email(user, otp_code, self.validated_data['client_app'])
        result = {'email_delivery': delivery.get('provider', 'unknown')}
        if _should_return_development_reset_code():
            if self.validated_data['client_app'] == self.CLIENT_MOBILE:
                result['reset_code'] = otp_code
            elif self.validated_data['client_app'] == self.CLIENT_WEB:
                result['reset_link'] = build_password_reset_link(user, otp_code, self.CLIENT_WEB)
                result['email_delivery_note'] = 'Development email mode detected. Configure SMTP or SendGrid in backend/.env to deliver this email to an inbox; for now, the reset email was printed to the backend console.'
        return result


def _user_can_reset_from_client(user, client_app):
    if client_app == PasswordResetRequestSerializer.CLIENT_MOBILE:
        return user.role == User.Role.APPLICANT
    if client_app == PasswordResetRequestSerializer.CLIENT_WEB:
        return user.role in PasswordResetRequestSerializer.STAFF_ROLES
    return False


def _should_return_development_reset_code():
    return is_development_email_backend()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    client_app = serializers.ChoiceField(
        choices=(PasswordResetRequestSerializer.CLIENT_WEB, PasswordResetRequestSerializer.CLIENT_MOBILE)
    )
    otp_code = serializers.CharField(max_length=6, min_length=6, required=False)
    reset_token = serializers.CharField(max_length=6, min_length=6, required=False)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        user = User.objects.filter(email__iexact=attrs['email']).first()
        if not user or not _user_can_reset_from_client(user, attrs['client_app']):
            raise serializers.ValidationError({'detail': 'Invalid OTP or email.'})

        reset_secret = attrs.get('otp_code') or attrs.get('reset_token')
        if not reset_secret:
            raise serializers.ValidationError({'detail': 'Invalid reset link or email.'})

        otp = PasswordResetOTP.objects.filter(
            user=user,
            otp_code=reset_secret,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).order_by('-created_at').first()

        if not otp:
            raise serializers.ValidationError({'detail': 'Invalid OTP or email.'})

        attrs['user'] = user
        attrs['otp'] = otp
        return attrs

    def save(self):
        user = self.validated_data['user']
        otp = self.validated_data['otp']

        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        otp.is_used = True
        otp.save(update_fields=['is_used'])


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value, self.context['request'].user)
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': 'Current password is incorrect.'})
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({'new_password': 'New password must be different from the current password.'})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


ALLOWED_RESUME_CONTENT_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}


class ResumeUploadSerializer(serializers.ModelSerializer):
    resume_file = serializers.FileField(write_only=True)

    class Meta:
        model = ApplicantProfile
        fields = ['resume_file']

    def validate_resume_file(self, file):
        max_size = 5 * 1024 * 1024
        if file.size > max_size:
            raise serializers.ValidationError('Resume file must not exceed 5MB.')

        filename = file.name.lower()
        if not (filename.endswith('.pdf') or filename.endswith('.docx')):
            raise serializers.ValidationError('Only PDF and DOCX files are allowed.')

        content_type = getattr(file, 'content_type', '')
        if content_type and content_type not in ALLOWED_RESUME_CONTENT_TYPES:
            raise serializers.ValidationError('Unsupported resume content type.')
        return file


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self):
        token = RefreshToken(self.validated_data['refresh'])
        token.blacklist()
