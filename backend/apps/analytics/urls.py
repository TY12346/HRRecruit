from django.urls import path

from .views import (
    HiringManagerDashboardAPIView,
    InterviewerDashboardAPIView,
    JobFunnelAPIView,
    OrganizationOverviewAPIView,
    RecruiterDashboardAPIView,
)

urlpatterns = [
    path('recruiter/dashboard/', RecruiterDashboardAPIView.as_view(), name='analytics-recruiter-dashboard'),
    path('interviewer/dashboard/', InterviewerDashboardAPIView.as_view(), name='analytics-interviewer-dashboard'),
    path('hiring-manager/dashboard/', HiringManagerDashboardAPIView.as_view(), name='analytics-hiring-manager-dashboard'),
    path('jobs/<int:job_id>/funnel/', JobFunnelAPIView.as_view(), name='analytics-job-funnel'),
    path('organization/overview/', OrganizationOverviewAPIView.as_view(), name='analytics-organization-overview'),
]
