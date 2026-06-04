from django.urls import path

from .views import (
    HRHeadDashboardAPIView,
    InterviewerDashboardAPIView,
    JobFunnelAPIView,
    OrganizationOverviewAPIView,
    RecruiterDashboardAPIView,
)

urlpatterns = [
    path('recruiter/dashboard/', RecruiterDashboardAPIView.as_view(), name='analytics-recruiter-dashboard'),
    path('interviewer/dashboard/', InterviewerDashboardAPIView.as_view(), name='analytics-interviewer-dashboard'),
    path('hr-head/dashboard/', HRHeadDashboardAPIView.as_view(), name='analytics-hr-head-dashboard'),
    path('jobs/<int:job_id>/funnel/', JobFunnelAPIView.as_view(), name='analytics-job-funnel'),
    path('organization/overview/', OrganizationOverviewAPIView.as_view(), name='analytics-organization-overview'),
]
