"""Role-protected analytics API views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
    hr_head_dashboard,
    interviewer_dashboard,
    job_funnel,
    organization_overview,
    recruiter_dashboard,
)


class RecruiterDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(recruiter_dashboard(request.user))


class InterviewerDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(interviewer_dashboard(request.user))


class HRHeadDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(hr_head_dashboard(request.user))


class JobFunnelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        return Response(job_funnel(request.user, job_id))


class OrganizationOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(organization_overview(request.user))
