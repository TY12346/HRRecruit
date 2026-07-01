import os
from datetime import datetime
from tempfile import NamedTemporaryFile

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.ai_services.linkedin_profile_importer import build_linkedin_profile_import
from apps.ai_services.resume_text_extractor import ResumeTextExtractionError, extract_resume_text

from .models import ApplicantEducation, ApplicantExperience, ApplicantResume, ApplicantSkill, User
from .serializers import (
    ApplicantRegisterSerializer,
    ApplicantResumeSerializer,
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

        temporary_pdf_path = None
        try:
            with NamedTemporaryFile(suffix='.pdf', delete=False) as temporary_pdf:
                temporary_pdf_path = temporary_pdf.name
                for chunk in linkedin_pdf.chunks():
                    temporary_pdf.write(chunk)
                temporary_pdf.flush()

            extracted_text = extract_resume_text(temporary_pdf_path)
        except ResumeTextExtractionError as exc:
            return Response({'linkedin_pdf': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            if temporary_pdf_path:
                try:
                    os.remove(temporary_pdf_path)
                except FileNotFoundError:
                    pass

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

        imported_skills = imported_profile.get('skills') or []
        if imported_skills:
            user.skills.all().delete()
            ApplicantSkill.objects.bulk_create(
                ApplicantSkill(applicant=user, skill_name=skill)
                for skill in imported_skills
            )

        imported_experience = imported_profile.get('experience') or []
        if imported_experience:
            user.experiences.all().delete()
            ApplicantExperience.objects.bulk_create(
                ApplicantExperience(
                    applicant=user,
                    job_title=experience.get('job_title') or imported_profile.get('headline', 'LinkedIn experience'),
                    company_name=experience.get('company_name', ''),
                    employment_type=experience.get('employment_type', ''),
                    start_date=_parse_linkedin_month_date(experience.get('start_date')),
                    location=experience.get('location', ''),
                )
                for experience in imported_experience
            )

        imported_education = imported_profile.get('education') or []
        if imported_education:
            user.educations.all().delete()
            ApplicantEducation.objects.bulk_create(
                ApplicantEducation(
                    applicant=user,
                    school_name=education.get('school_name', 'Imported from LinkedIn'),
                    degree_name=education.get('degree_name', ''),
                    field_of_study=education.get('field_of_study', ''),
                    start_date=_parse_linkedin_month_date(education.get('start_date')),
                    end_date=_parse_linkedin_month_date(education.get('end_date')),
                    grade=education.get('grade', ''),
                )
                for education in imported_education
            )

        return Response(
            {
                'message': 'LinkedIn profile PDF imported successfully.',
                'user': UserProfileSerializer(user).data,
                'extracted_profile': imported_profile,
            }
        )


class ResumeUploadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.APPLICANT:
            return Response({'detail': 'Only applicants can view resumes.'}, status=status.HTTP_403_FORBIDDEN)
        resumes = request.user.resumes.all()
        return Response(ApplicantResumeSerializer(resumes, many=True, context={'request': request}).data)

    def post(self, request):
        if request.user.role != User.Role.APPLICANT:
            return Response({'detail': 'Only applicants can upload resumes.'}, status=status.HTTP_403_FORBIDDEN)

        upload_data = request.data.copy()
        is_single_resume_upload = request.resolver_match.url_name == 'auth-resume-upload'
        if is_single_resume_upload:
            upload_data['is_default'] = True

        serializer = ResumeUploadSerializer(data=upload_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        resume = serializer.save()
        resume_data = ApplicantResumeSerializer(resume, context={'request': request}).data
        response_status = (
            status.HTTP_200_OK
            if is_single_resume_upload
            else status.HTTP_201_CREATED
        )
        return Response(
            {
                'message': 'Resume uploaded successfully.',
                'resume_file': resume.resume_file.url,
                'resume': resume_data,
            },
            status=response_status,
        )


class ApplicantResumeDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_resume(self, request, resume_id):
        if request.user.role != User.Role.APPLICANT:
            return None
        return get_object_or_404(ApplicantResume, id=resume_id, applicant=request.user)

    def patch(self, request, resume_id):
        if request.user.role != User.Role.APPLICANT:
            return Response({'detail': 'Only applicants can update resumes.'}, status=status.HTTP_403_FORBIDDEN)
        resume = self.get_resume(request, resume_id)
        title = request.data.get('title')
        update_fields = []
        if title is not None:
            resume.title = title.strip() or resume.resume_file.name.split('/')[-1]
            update_fields.append('title')
        if request.data.get('is_default') in (True, 'true', 'True', '1', 1):
            resume.is_default = True
            update_fields.append('is_default')
        if update_fields:
            resume.save(update_fields=update_fields)
            if resume.is_default:
                _sync_default_resume_to_profile(request.user)
        return Response(
            {
                'message': 'Resume updated successfully.',
                'resume': ApplicantResumeSerializer(resume, context={'request': request}).data,
            }
        )

    def delete(self, request, resume_id):
        if request.user.role != User.Role.APPLICANT:
            return Response({'detail': 'Only applicants can delete resumes.'}, status=status.HTTP_403_FORBIDDEN)
        resume = self.get_resume(request, resume_id)
        was_default = resume.is_default
        resume.delete()
        if was_default:
            replacement = request.user.resumes.order_by('-uploaded_at', '-id').first()
            if replacement:
                replacement.is_default = True
                replacement.save(update_fields=['is_default'])
            _sync_default_resume_to_profile(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


def _sync_default_resume_to_profile(applicant):
    profile = applicant.applicant_profile
    default_resume = applicant.resumes.filter(is_default=True).first()
    profile.resume_file = default_resume.resume_file if default_resume else None
    profile.save(update_fields=['resume_file', 'updated_at'])


def _parse_linkedin_month_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%B %Y').date().replace(day=1)
    except ValueError:
        return None
