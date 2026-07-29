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
    ApplicationSearchAPIView,
    ApplicationShortlistAPIView,
    ApplicationStatusHistoryAPIView,
    ApplicantProfileAPIView,
    ApplicantDirectoryDetailAPIView,
    EmployerInviteListCreateAPIView,
    EmployerInviteDeclineAPIView,
)

urlpatterns = [
    path('', ApplicationListAPIView.as_view(), name='application-list'),
    path('search/', ApplicationSearchAPIView.as_view(), name='application-search'),
    path('directory/<str:applicant_id>/', ApplicantDirectoryDetailAPIView.as_view(), name='applicant-directory-detail'),
    path('employer-invites/', EmployerInviteListCreateAPIView.as_view(), name='employer-invite-list-create'),
    path('employer-invites/<str:invite_id>/decline/', EmployerInviteDeclineAPIView.as_view(), name='employer-invite-decline'),
    path('<str:application_id>/', ApplicationDetailAPIView.as_view(), name='application-detail'),
    path('<str:application_id>/screen/', ApplicationScreenAPIView.as_view(), name='application-screen'),
    path('<str:application_id>/applicant-profile/', ApplicantProfileAPIView.as_view(), name='application-applicant-profile'),
    path('<str:application_id>/resume/', ApplicationResumeAPIView.as_view(), name='application-resume'),
    path('<str:application_id>/shortlist/', ApplicationShortlistAPIView.as_view(), name='application-shortlist'),
    path('<str:application_id>/assign-interviewer/', AssignInterviewerAPIView.as_view(), name='application-assign-interviewer'),
    path('<str:application_id>/scheduling-request/', CreateSchedulingRequestAPIView.as_view(), name='application-create-scheduling-request'),
    path('<str:application_id>/interview-available-dates/', ApplicationAvailableInterviewDatesAPIView.as_view(), name='application-interview-available-dates'),
    path('<str:application_id>/interview-available-slots/', ApplicationAvailableInterviewSlotsAPIView.as_view(), name='application-interview-available-slots'),
    path('<str:application_id>/book-interview-slot/', ApplicationBookInterviewSlotAPIView.as_view(), name='application-book-interview-slot'),
    path('<str:application_id>/reject/', ApplicationRejectAPIView.as_view(), name='application-reject'),
    path('<str:application_id>/remark/', ApplicationRemarkAPIView.as_view(), name='application-remark'),
    path('<str:application_id>/status-history/', ApplicationStatusHistoryAPIView.as_view(), name='application-status-history'),
    path('<str:application_id>/hiring-decision/', HiringDecisionSubmitAPIView.as_view(), name='application-hiring-decision'),
    path('<str:application_id>/job-offer/', JobOfferCreateAPIView.as_view(), name='application-job-offer'),
]
