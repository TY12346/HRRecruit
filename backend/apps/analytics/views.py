"""Role-protected analytics API views."""

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .reports import ReportGenerationError, build_analytics_summary_pdf
from .services import (
    hiring_manager_dashboard,
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


class HiringManagerDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(hiring_manager_dashboard(request.user))


class JobFunnelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        return Response(job_funnel(request.user, job_id))


class OrganizationOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(organization_overview(request.user))


class AnalyticsReportPDFAPIView(APIView):
    permission_classes = [IsAuthenticated]
    report_type = None
    dashboard_builder = None
    filename = None

    def get(self, request):
        dashboard = self.dashboard_builder(request.user)
        try:
            pdf_content = build_analytics_summary_pdf(self.report_type, dashboard, request.user)
        except ReportGenerationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'
        return response


class RecruiterSummaryPDFAPIView(AnalyticsReportPDFAPIView):
    report_type = 'recruiter'
    dashboard_builder = staticmethod(recruiter_dashboard)
    filename = 'recruiter-summary.pdf'


class InterviewerSummaryPDFAPIView(AnalyticsReportPDFAPIView):
    report_type = 'interviewer'
    dashboard_builder = staticmethod(interviewer_dashboard)
    filename = 'interviewer-summary.pdf'


class HiringManagerSummaryPDFAPIView(AnalyticsReportPDFAPIView):
    report_type = 'hr_head'
    dashboard_builder = staticmethod(hiring_manager_dashboard)
    filename = 'hiring-manager-summary.pdf'
