"""Role-protected and organization-isolated job application APIs."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_services.resume_text_extractor import ResumeTextExtractionError
from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

from .models import JobApplication
from .serializers import ApplicationStageHistorySerializer, JobApplicationSerializer
from .services import schedule_resume_screening, screen_job_application


def get_active_membership(user, role):
    return OrganizationMembership.objects.filter(
        user=user,
        role=role,
        status=OrganizationMembership.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    ).select_related('organization').first()


def visible_applications_for(user):
    applications = JobApplication.objects.select_related(
        'job', 'job__organization', 'job__recruiter', 'applicant', 'applicant__applicant_profile'
    )
    if user.role == User.Role.APPLICANT:
        return applications.filter(applicant=user)
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        if membership:
            return applications.filter(job__organization=membership.organization, job__recruiter=user)
    elif user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
        if membership:
            return applications.filter(job__organization=membership.organization)
    return applications.none()


def ensure_application_viewer_role(user):
    if user.role not in (User.Role.APPLICANT, User.Role.RECRUITER, User.Role.HR_HEAD):
        raise PermissionDenied('Your role cannot view job applications.')


class JobApplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can apply for jobs.')
        job = get_object_or_404(
            JobPosting.objects.select_related('organization'),
            id=job_id,
            status=JobPosting.Status.OPEN,
            organization__status=Organization.Status.ACTIVE,
        )
        application, created = JobApplication.objects.get_or_create(job=job, applicant=request.user)
        if not created:
            raise ValidationError({'job': 'You have already applied for this job.'})

        # Screening remains recruiter-triggered; submission must not make an automated decision.
        schedule_resume_screening(application)
        return Response(JobApplicationSerializer(application, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def delete(self, request, job_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can withdraw job applications.')
        application = get_object_or_404(JobApplication, job_id=job_id, applicant=request.user)
        if application.status not in (JobApplication.Status.SUBMITTED, JobApplication.Status.SCREENED):
            raise ValidationError({'status': 'Applications can be withdrawn only while submitted or screened.'})
        application.change_status(
            JobApplication.Status.WITHDRAWN,
            changed_by=request.user,
            note='Withdrawn by applicant.',
        )
        return Response(JobApplicationSerializer(application, context={'request': request}).data)


class ApplicationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_application_viewer_role(request.user)
        applications = visible_applications_for(request.user)
        return Response(JobApplicationSerializer(applications, many=True, context={'request': request}).data)


class ApplicationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        ensure_application_viewer_role(request.user)
        application = get_object_or_404(visible_applications_for(request.user), id=application_id)
        return Response(JobApplicationSerializer(application, context={'request': request}).data)


class ApplicationStatusHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        ensure_application_viewer_role(request.user)
        application = get_object_or_404(visible_applications_for(request.user), id=application_id)
        history = application.stage_history.select_related('changed_by')
        return Response(ApplicationStageHistorySerializer(history, many=True).data)


class ApplicationScreenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can screen job applications.')

        application = get_object_or_404(visible_applications_for(request.user), id=application_id)
        try:
            resume_file = application.applicant.applicant_profile.resume_file
            if not resume_file:
                raise ValidationError({'resume_file': 'The applicant must upload a resume before screening.'})
            application = screen_job_application(application, changed_by=request.user)
        except ResumeTextExtractionError as exc:
            raise ValidationError({'resume_file': str(exc)}) from exc

        return Response(JobApplicationSerializer(application, context={'request': request}).data)
