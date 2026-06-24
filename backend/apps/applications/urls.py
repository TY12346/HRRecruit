from django.urls import path

from apps.hiring.views import HiringDecisionSubmitAPIView, JobOfferCreateAPIView
from apps.interviews.views import (
    ApplicationAvailableInterviewDatesAPIView,
    ApplicationAvailableInterviewSlotsAPIView,
    ApplicationBookInterviewSlotAPIView,
    AssignInterviewerAPIView,
    CreateSchedulingRequestAPIView,
)

from .views import (
    ApplicationDetailAPIView,
    ApplicationListAPIView,
    ApplicationRejectAPIView,
    ApplicationResumeAPIView,
    ApplicationRemarkAPIView,
    ApplicationScreenAPIView,
    ApplicationShortlistAPIView,
    ApplicationStatusHistoryAPIView,
    CandidateProfileAPIView,
)

urlpatterns = [
    path('', ApplicationListAPIView.as_view(), name='application-list'),
    path('<int:application_id>/', ApplicationDetailAPIView.as_view(), name='application-detail'),
    path('<int:application_id>/screen/', ApplicationScreenAPIView.as_view(), name='application-screen'),
    path('<int:application_id>/candidate-profile/', CandidateProfileAPIView.as_view(), name='application-candidate-profile'),
    path('<int:application_id>/resume/', ApplicationResumeAPIView.as_view(), name='application-resume'),
    path('<int:application_id>/shortlist/', ApplicationShortlistAPIView.as_view(), name='application-shortlist'),
    path('<int:application_id>/assign-interviewer/', AssignInterviewerAPIView.as_view(), name='application-assign-interviewer'),
    path('<int:application_id>/scheduling-request/', CreateSchedulingRequestAPIView.as_view(), name='application-create-scheduling-request'),
    path('<int:application_id>/interview-available-dates/', ApplicationAvailableInterviewDatesAPIView.as_view(), name='application-interview-available-dates'),
    path('<int:application_id>/interview-available-slots/', ApplicationAvailableInterviewSlotsAPIView.as_view(), name='application-interview-available-slots'),
    path('<int:application_id>/book-interview-slot/', ApplicationBookInterviewSlotAPIView.as_view(), name='application-book-interview-slot'),
    path('<int:application_id>/reject/', ApplicationRejectAPIView.as_view(), name='application-reject'),
    path('<int:application_id>/remark/', ApplicationRemarkAPIView.as_view(), name='application-remark'),
    path('<int:application_id>/status-history/', ApplicationStatusHistoryAPIView.as_view(), name='application-status-history'),
    path('<int:application_id>/hiring-decision/', HiringDecisionSubmitAPIView.as_view(), name='application-hiring-decision'),
    path('<int:application_id>/job-offer/', JobOfferCreateAPIView.as_view(), name='application-job-offer'),
]
