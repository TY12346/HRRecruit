from tempfile import NamedTemporaryFile

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.ai_services.linkedin_profile_importer import build_linkedin_profile_import
from apps.ai_services.resume_text_extractor import ResumeTextExtractionError, extract_resume_text

from .models import User
from .serializers import (
    ApplicantRegisterSerializer,
    ChangePasswordSerializer,
    LinkedInProfilePdfUploadSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    RegisterSerializer,
    ResumeUploadSerializer,
    UserProfileSerializer,
)


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': 'Registration successful.',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class ApplicantRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ApplicantRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': 'Applicant registration successful.',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': 'Login successful.',
                'user': UserProfileSerializer(user).data,
                'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)},
            }
        )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Logout successful.'})


class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Profile updated successfully.', 'user': serializer.data})


class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully.'})


class PasswordResetRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save() or {}
        response_data = {'message': 'If the email exists, password reset instructions have been sent.'}
        response_data.update(result)
        return Response(response_data)


class PasswordResetVerifyAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message': 'OTP verified successfully.'})


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password reset successful.'})


class LinkedInProfilePdfImportAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != User.Role.APPLICANT:
            return Response(
                {'detail': 'Only applicants can import LinkedIn profile PDFs.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = LinkedInProfilePdfUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        linkedin_pdf = serializer.validated_data['linkedin_pdf']

        try:
            with NamedTemporaryFile(suffix='.pdf') as temporary_pdf:
                for chunk in linkedin_pdf.chunks():
                    temporary_pdf.write(chunk)
                temporary_pdf.flush()
                extracted_text = extract_resume_text(temporary_pdf.name)
        except ResumeTextExtractionError as exc:
            return Response({'linkedin_pdf': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        imported_profile = build_linkedin_profile_import(extracted_text)
        user = request.user
        profile = user.applicant_profile

        if imported_profile['name']:
            user.full_name = imported_profile['name']
            user.save(update_fields=['full_name'])

        profile.personal_summary = imported_profile['summary']
        update_profile_fields = ['personal_summary']
        if imported_profile['linkedin_url']:
            profile.linkedin_url = imported_profile['linkedin_url']
            update_profile_fields.append('linkedin_url')
        profile.save(update_fields=update_profile_fields)

        return Response(
            {
                'message': 'LinkedIn profile PDF imported successfully.',
                'user': UserProfileSerializer(user).data,
                'extracted_profile': imported_profile,
            }
        )


class ResumeUploadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != User.Role.APPLICANT:
            return Response({'detail': 'Only applicants can upload resumes.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ResumeUploadSerializer(request.user.applicant_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Resume uploaded successfully.', 'resume_file': request.user.applicant_profile.resume_file.url})
