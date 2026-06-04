from django.urls import path

from .views import HRHeadSummaryPDFAPIView, InterviewerSummaryPDFAPIView, RecruiterSummaryPDFAPIView

urlpatterns = [
    path('recruiter-summary.pdf', RecruiterSummaryPDFAPIView.as_view(), name='reports-recruiter-summary-pdf'),
    path('interviewer-summary.pdf', InterviewerSummaryPDFAPIView.as_view(), name='reports-interviewer-summary-pdf'),
    path('hr-head-summary.pdf', HRHeadSummaryPDFAPIView.as_view(), name='reports-hr-head-summary-pdf'),
]
