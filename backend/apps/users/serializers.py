import random

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.email_service import send_password_reset_otp_email

from .models import ApplicantProfile, PasswordResetOTP, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'password']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            role=User.Role.HR_HEAD,
            **validated_data,
        )
        return user


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
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data['email']
        user = User.objects.filter(email=email).first()
        if not user:
            return

        otp_code = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        PasswordResetOTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at)

        send_password_reset_otp_email(user, otp_code)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        user = User.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError({'detail': 'Invalid OTP or email.'})

        otp = PasswordResetOTP.objects.filter(
            user=user,
            otp_code=attrs['otp_code'],
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
