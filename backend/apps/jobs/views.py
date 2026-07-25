"""Role-protected and organization-isolated job posting APIs."""

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services import SubscriptionLimitError, enforce_open_job_limit
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User
from django.utils import timezone

from .models import JobPosting, JobRequisition, SavedJobPosting
from .serializers import (
    InterviewEvaluationFormSerializer,
    JobPostingSerializer,
    JobRequirementConfigurationSerializer,
    JobRequisitionRejectSerializer,
    JobRequisitionSerializer,
)
from apps.hiring.services import refresh_job_readiness


def get_active_membership(user, role=None):
    filters = {
        'user': user,
        'status': OrganizationMembership.Status.ACTIVE,
        'organization__status': Organization.Status.ACTIVE,
    }
    if role:
        filters['role'] = role
    return OrganizationMembership.objects.filter(**filters).select_related('organization').first()


def visible_jobs_for(user):
    jobs = JobPosting.objects.select_related('organization', 'recruiter').prefetch_related(
        'requirements', 'interview_evaluation_form__criteria'
    )
    if user.role == User.Role.APPLICANT:
        return jobs.filter(status=JobPosting.Status.OPEN, organization__status=Organization.Status.ACTIVE)
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        return jobs.filter(organization=membership.organization, recruiter=user) if membership else jobs.none()
    elif user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
    else:
        return jobs.none()
    return jobs.filter(organization=membership.organization) if membership else jobs.none()



def enforce_job_opening_allowed(organization, requested_status, current_job=None):
    if requested_status != JobPosting.Status.OPEN:
        return
    if current_job and current_job.status == JobPosting.Status.OPEN:
        return
    open_jobs = JobPosting.objects.filter(organization=organization, status=JobPosting.Status.OPEN)
    if current_job:
        open_jobs = open_jobs.exclude(id=current_job.id)
    try:
        enforce_open_job_limit(organization, open_jobs.count())
    except SubscriptionLimitError as exc:
        raise ValidationError({'status': [str(exc)]}) from exc


def enforce_job_ready_for_open(job, requested_status):
    if requested_status != JobPosting.Status.OPEN or job.status == JobPosting.Status.OPEN:
        return
    if not job.requirements.exists():
        raise ValidationError({'status': ['Configure job requirements before posting this job opening.']})
    if (
        not hasattr(job, 'interview_evaluation_form')
        or not job.interview_evaluation_form.criteria.exists()
    ):
        raise ValidationError({
            'status': ['Configure a non-empty interview evaluation scorecard before posting this job opening.']
        })


def enforce_job_status_transition(job, requested_status):
    """Keep recruiter-managed job status changes moving forward only."""
    if requested_status == job.status:
        return

    allowed_transitions = {
        JobPosting.Status.DRAFTING: {JobPosting.Status.OPEN},
        JobPosting.Status.OPEN: {JobPosting.Status.CLOSED},
    }
    if requested_status not in allowed_transitions.get(job.status, set()):
        raise ValidationError({
            'status': [
                f'Job status cannot be changed from {job.get_status_display()} '
                f'to {JobPosting.Status(requested_status).label}. Status changes cannot be reversed.'
            ]
        })


def recruiter_job_or_404(user, job_id):
    membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
    if not membership:
        raise PermissionDenied('An active recruiter organization membership is required.')
    return get_object_or_404(JobPosting, id=job_id, organization=membership.organization, recruiter=user)


def visible_requisitions_for(user):
    requisitions = JobRequisition.objects.select_related('organization', 'recruiter', 'reviewed_by', 'job_posting')
    if user.role == User.Role.RECRUITER:
        membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
        return requisitions.filter(organization=membership.organization, recruiter=user) if membership else requisitions.none()
    if user.role == User.Role.HR_HEAD:
        membership = get_active_membership(user, OrganizationMembership.Role.HR_HEAD)
        return requisitions.filter(organization=membership.organization) if membership else requisitions.none()
    return requisitions.none()


def hr_requisition_or_404(user, requisition_id):
    if user.role != User.Role.HR_HEAD:
        raise PermissionDenied('Only hiring managers can review job requisitions.')
    return get_object_or_404(visible_requisitions_for(user), id=requisition_id)


class JobRequisitionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in (User.Role.RECRUITER, User.Role.HR_HEAD):
            raise PermissionDenied('Your role cannot view job requisitions.')
        return Response(JobRequisitionSerializer(visible_requisitions_for(request.user), many=True, context={'request': request}).data)

    def post(self, request):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can submit job requisitions.')
        membership = get_active_membership(request.user, OrganizationMembership.Role.RECRUITER)
        if not membership:
            raise PermissionDenied('An active recruiter organization membership is required.')
        serializer = JobRequisitionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        requisition = serializer.save(organization=membership.organization, recruiter=request.user)
        return Response(JobRequisitionSerializer(requisition, context={'request': request}).data, status=status.HTTP_201_CREATED)


class JobRequisitionApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, requisition_id):
        requisition = hr_requisition_or_404(request.user, requisition_id)
        if requisition.status != JobRequisition.Status.PENDING:
            raise ValidationError({'status': 'Only pending requisitions can be approved.'})
        job = JobPosting.objects.create(
            organization=requisition.organization,
            recruiter=requisition.recruiter,
            title=requisition.title,
            description=requisition.description,
            employment_type=requisition.employment_type,
            approximate_salary=requisition.approximate_salary,
            salary_range=requisition.salary_range,
            location=requisition.location,
            core_responsibilities=requisition.core_responsibilities,
            requirements_qualifications=requisition.requirements_qualifications,
            department=requisition.department,
            custom_department=requisition.custom_department,
            target_start_date=requisition.target_start_date,
            benefits_perks=requisition.benefits_perks,
            position_status=requisition.position_status,
            reason_for_hire=requisition.reason_for_hire,
            impact_of_not_hiring=requisition.impact_of_not_hiring,
            status=JobPosting.Status.DRAFTING,
        )
        requisition.status = JobRequisition.Status.APPROVED
        requisition.reviewed_by = request.user
        requisition.reviewed_at = timezone.now()
        requisition.job_posting = job
        requisition.rejection_reason = ''
        requisition.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'job_posting', 'rejection_reason', 'updated_at'])
        return Response(JobRequisitionSerializer(requisition, context={'request': request}).data)


class JobRequisitionRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, requisition_id):
        requisition = hr_requisition_or_404(request.user, requisition_id)
        if requisition.status != JobRequisition.Status.PENDING:
            raise ValidationError({'status': 'Only pending requisitions can be rejected.'})
        serializer = JobRequisitionRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requisition.status = JobRequisition.Status.REJECTED
        requisition.rejection_reason = serializer.validated_data['reason']
        requisition.reviewed_by = request.user
        requisition.reviewed_at = timezone.now()
        requisition.save(update_fields=['status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'updated_at'])
        return Response(JobRequisitionSerializer(requisition, context={'request': request}).data)


class JobListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in (User.Role.APPLICANT, User.Role.RECRUITER, User.Role.HR_HEAD):
            raise PermissionDenied('Your role cannot view job postings.')
        jobs = visible_jobs_for(request.user)
        if request.user.role == User.Role.APPLICANT:
            search = request.query_params.get('search', '').strip()
            if search:
                jobs = jobs.filter(Q(title__icontains=search) | Q(description__icontains=search))
            for field in ('title', 'location', 'employment_type'):
                value = request.query_params.get(field, '').strip()
                if value:
                    jobs = jobs.filter(**{f'{field}__icontains': value})
        return Response(JobPostingSerializer(jobs, many=True, context={'request': request}).data)

    def post(self, request):
        raise PermissionDenied('Recruiters must submit a job requisition for hiring manager approval before a job posting is created.')


class JobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(visible_jobs_for(request.user), id=job_id)
        return Response(JobPostingSerializer(job, context={'request': request}).data)

    def patch(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can update job postings.')
        job = recruiter_job_or_404(request.user, job_id)
        serializer = JobPostingSerializer(job, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        requested_status = serializer.validated_data.get('status', job.status)
        enforce_job_status_transition(job, requested_status)
        enforce_job_ready_for_open(job, requested_status)
        enforce_job_opening_allowed(job.organization, requested_status, current_job=job)
        if requested_status == JobPosting.Status.OPEN and job.requirements_locked_at is None:
            serializer.save(requirements_locked_at=timezone.now())
        else:
            serializer.save()
        return Response(serializer.data)

    def delete(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can delete job postings.')
        job = recruiter_job_or_404(request.user, job_id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobCloseIntakeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can close application intake.')
        job = recruiter_job_or_404(request.user, job_id)
        if job.status != JobPosting.Status.OPEN:
            raise ValidationError({'status': 'Application intake can only be closed for an open job posting.'})
        job.status = JobPosting.Status.CLOSED
        job.save(update_fields=['status', 'updated_at'])
        readiness = refresh_job_readiness(job)
        return Response({'job': JobPostingSerializer(job, context={'request': request}).data, 'readiness': readiness})


class JobDuplicateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        raise PermissionDenied('Recruiters must submit a job requisition for hiring manager approval before a new job posting is created.')


class JobRequirementsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can configure job requirements.')
        job = recruiter_job_or_404(request.user, job_id)
        if job.requirements_locked_at is not None or job.status != JobPosting.Status.DRAFTING:
            raise ValidationError({
                'requirements': ['Job requirements cannot be changed once this job has been posted.']
            })
        serializer = JobRequirementConfigurationSerializer(data=request.data, context={'job': job})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(JobPostingSerializer(job, context={'request': request}).data, status=status.HTTP_201_CREATED)


class JobEvaluationFormAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can create interview evaluation scorecards.')
        job = recruiter_job_or_404(request.user, job_id)
        form = getattr(job, 'interview_evaluation_form', None)
        is_update = form is not None
        serializer = InterviewEvaluationFormSerializer(form, data=request.data) if form else InterviewEvaluationFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form = serializer.save(job=job) if form is None else serializer.save()
        response_status = status.HTTP_200_OK if is_update else status.HTTP_201_CREATED
        return Response(InterviewEvaluationFormSerializer(form).data, status=response_status)


class SavedJobListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can view saved jobs.')
        jobs = visible_jobs_for(request.user).filter(saved_by_applicants__applicant=request.user)
        return Response(JobPostingSerializer(jobs, many=True, context={'request': request}).data)


class JobSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can save jobs.')
        job = get_object_or_404(visible_jobs_for(request.user), id=job_id)
        saved_job, created = SavedJobPosting.objects.get_or_create(applicant=request.user, job=job)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({'message': 'Job saved successfully.', 'saved_at': saved_job.saved_at}, status=response_status)

    def delete(self, request, job_id):
        if request.user.role != User.Role.APPLICANT:
            raise PermissionDenied('Only applicants can unsave jobs.')
        deleted, _ = SavedJobPosting.objects.filter(applicant=request.user, job_id=job_id).delete()
        if not deleted:
            return Response({'detail': 'Saved job not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
