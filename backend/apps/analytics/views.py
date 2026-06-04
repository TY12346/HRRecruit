"""Role-protected analytics API views."""

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .reports import build_analytics_summary_pdf
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


class AnalyticsReportPDFAPIView(APIView):
    permission_classes = [IsAuthenticated]
    report_type = None
    dashboard_builder = None
    filename = None

    def get(self, request):
        dashboard = self.dashboard_builder(request.user)
        pdf_content = build_analytics_summary_pdf(self.report_type, dashboard, request.user)
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


class HRHeadSummaryPDFAPIView(AnalyticsReportPDFAPIView):
    report_type = 'hr_head'
    dashboard_builder = staticmethod(hr_head_dashboard)
    filename = 'hr-head-summary.pdf'
