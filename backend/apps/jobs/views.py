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

from .models import EvaluationCriterion, InterviewEvaluationForm, JobPosting, JobRequirement, SavedJobPosting
from .serializers import (
    InterviewEvaluationFormSerializer,
    JobPostingSerializer,
    JobRequirementConfigurationSerializer,
)


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
        raise ValidationError({'status': str(exc)}) from exc


def recruiter_job_or_404(user, job_id):
    membership = get_active_membership(user, OrganizationMembership.Role.RECRUITER)
    if not membership:
        raise PermissionDenied('An active recruiter organization membership is required.')
    return get_object_or_404(JobPosting, id=job_id, organization=membership.organization)


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
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can create job postings.')
        membership = get_active_membership(request.user, OrganizationMembership.Role.RECRUITER)
        if not membership:
            raise PermissionDenied('An active recruiter organization membership is required.')
        serializer = JobPostingSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        enforce_job_opening_allowed(
            membership.organization, serializer.validated_data.get('status', JobPosting.Status.DRAFT)
        )
        job = serializer.save(organization=membership.organization, recruiter=request.user)
        return Response(JobPostingSerializer(job, context={'request': request}).data, status=status.HTTP_201_CREATED)


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
        enforce_job_opening_allowed(
            job.organization, serializer.validated_data.get('status', job.status), current_job=job
        )
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can delete job postings.')
        job = recruiter_job_or_404(request.user, job_id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobDuplicateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can duplicate job postings.')
        source = recruiter_job_or_404(request.user, job_id)
        duplicate = JobPosting.objects.create(
            organization=source.organization,
            recruiter=request.user,
            title=f'{source.title} (Copy)',
            description=source.description,
            employment_type=source.employment_type,
            approximate_salary=source.approximate_salary,
            location=source.location,
            status=JobPosting.Status.DRAFT,
        )
        JobRequirement.objects.bulk_create(
            JobRequirement(
                job=duplicate,
                requirement_type=requirement.requirement_type,
                description=requirement.description,
                weight_score=requirement.weight_score,
                minimum_threshold=requirement.minimum_threshold,
            )
            for requirement in source.requirements.all()
        )
        try:
            source_form = source.interview_evaluation_form
        except InterviewEvaluationForm.DoesNotExist:
            source_form = None
        if source_form:
            duplicate_form = InterviewEvaluationForm.objects.create(job=duplicate, title=source_form.title)
            EvaluationCriterion.objects.bulk_create(
                EvaluationCriterion(
                    form=duplicate_form,
                    criterion_name=criterion.criterion_name,
                    description=criterion.description,
                    max_score=criterion.max_score,
                    weight_score=criterion.weight_score,
                )
                for criterion in source_form.criteria.all()
            )
        return Response(JobPostingSerializer(duplicate, context={'request': request}).data, status=status.HTTP_201_CREATED)


class JobRequirementsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can configure job requirements.')
        job = recruiter_job_or_404(request.user, job_id)
        serializer = JobRequirementConfigurationSerializer(data=request.data, context={'job': job})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(JobPostingSerializer(job, context={'request': request}).data, status=status.HTTP_201_CREATED)


class JobEvaluationFormAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if request.user.role != User.Role.RECRUITER:
            raise PermissionDenied('Only recruiters can create job evaluation forms.')
        job = recruiter_job_or_404(request.user, job_id)
        if hasattr(job, 'interview_evaluation_form'):
            return Response({'detail': 'This job already has an evaluation form.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = InterviewEvaluationFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form = serializer.save(job=job)
        return Response(InterviewEvaluationFormSerializer(form).data, status=status.HTTP_201_CREATED)


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
