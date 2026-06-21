from django.urls import path

from .views import (
    ApplicantRegisterAPIView,
    ChangePasswordAPIView,
    LinkedInProfilePdfImportAPIView,
    LoginAPIView,
    LogoutAPIView,
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
    PasswordResetVerifyAPIView,
    ProfileAPIView,
    RegisterAPIView,
    ResumeUploadAPIView,
)

urlpatterns = [
    path('auth/register/', RegisterAPIView.as_view(), name='auth-register'),
    path('auth/register-applicant/', ApplicantRegisterAPIView.as_view(), name='auth-register-applicant'),
    path('auth/login/', LoginAPIView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='auth-logout'),
    path('auth/profile/', ProfileAPIView.as_view(), name='auth-profile'),
    path('auth/password/change/', ChangePasswordAPIView.as_view(), name='auth-password-change'),
    path('auth/password-reset/request/', PasswordResetRequestAPIView.as_view(), name='auth-password-reset-request'),
    path('auth/password-reset/verify/', PasswordResetVerifyAPIView.as_view(), name='auth-password-reset-verify'),
    path('auth/password-reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='auth-password-reset-confirm'),
    path('auth/resume/upload/', ResumeUploadAPIView.as_view(), name='auth-resume-upload'),
    path('auth/linkedin-profile/import/', LinkedInProfilePdfImportAPIView.as_view(), name='auth-linkedin-profile-import'),
]
