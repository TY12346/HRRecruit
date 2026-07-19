from django.urls import path

from .views import HiringManagerSummaryPDFAPIView, InterviewerSummaryPDFAPIView, RecruiterSummaryPDFAPIView

urlpatterns = [
    path('recruiter-summary.pdf', RecruiterSummaryPDFAPIView.as_view(), name='reports-recruiter-summary-pdf'),
    path('interviewer-summary.pdf', InterviewerSummaryPDFAPIView.as_view(), name='reports-interviewer-summary-pdf'),
    path('hiring-manager-summary.pdf', HiringManagerSummaryPDFAPIView.as_view(), name='reports-hiring-manager-summary-pdf'),
]
