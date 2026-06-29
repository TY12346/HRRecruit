from django.urls import path

from apps.evaluations.views import (
    InterviewEvaluationDetailAPIView,
    InterviewEvaluationSubmitAPIView,
    InterviewRecordingUploadAPIView,
)
from .views import (
    AssignedInterviewListAPIView,
    BookSchedulingRequestAPIView,
    GoogleCalendarConnectAPIView,
    GoogleCalendarDisconnectAPIView,
    GoogleCalendarOAuthCallbackAPIView,
    GoogleCalendarStatusAPIView,
    InterviewDetailAPIView,
    InterviewListAPIView,
    InterviewSchedulingRequestListAPIView,
    InterviewerAvailabilityPatternDetailAPIView,
    InterviewerAvailabilityPatternListCreateAPIView,
    InterviewerAvailabilitySlotDetailAPIView,
    InterviewerAvailabilitySlotListCreateAPIView,
    InterviewerUnavailableDateDetailAPIView,
    InterviewerUnavailableDateListCreateAPIView,
)

urlpatterns = [
    path('', InterviewListAPIView.as_view(), name='interview-list'),
    path('assigned/', AssignedInterviewListAPIView.as_view(), name='interview-assigned-list'),
    path('calendar/google/status/', GoogleCalendarStatusAPIView.as_view(), name='google-calendar-status'),
    path('calendar/google/connect/', GoogleCalendarConnectAPIView.as_view(), name='google-calendar-connect'),
    path('calendar/google/callback/', GoogleCalendarOAuthCallbackAPIView.as_view(), name='google-calendar-callback'),
    path('calendar/google/disconnect/', GoogleCalendarDisconnectAPIView.as_view(), name='google-calendar-disconnect'),
    path('availability/patterns/', InterviewerAvailabilityPatternListCreateAPIView.as_view(), name='interviewer-availability-pattern-list-create'),
    path('availability/patterns/<int:pattern_id>/', InterviewerAvailabilityPatternDetailAPIView.as_view(), name='interviewer-availability-pattern-detail'),
    path('availability/unavailable-dates/', InterviewerUnavailableDateListCreateAPIView.as_view(), name='interviewer-unavailable-date-list-create'),
    path('availability/unavailable-dates/<int:unavailable_date_id>/', InterviewerUnavailableDateDetailAPIView.as_view(), name='interviewer-unavailable-date-detail'),
    path('availability/', InterviewerAvailabilitySlotListCreateAPIView.as_view(), name='interviewer-availability-list-create'),
    path('availability/<int:slot_id>/', InterviewerAvailabilitySlotDetailAPIView.as_view(), name='interviewer-availability-detail'),
    path('scheduling-requests/', InterviewSchedulingRequestListAPIView.as_view(), name='interview-scheduling-request-list'),
    path('scheduling-requests/<int:scheduling_request_id>/book/', BookSchedulingRequestAPIView.as_view(), name='interview-scheduling-request-book'),
    path('<int:interview_id>/', InterviewDetailAPIView.as_view(), name='interview-detail'),
    path('<int:interview_id>/recordings/', InterviewRecordingUploadAPIView.as_view(), name='interview-recording-upload'),
    path('<int:interview_id>/evaluations/', InterviewEvaluationSubmitAPIView.as_view(), name='interview-evaluation-submit'),
    path('<int:interview_id>/evaluation-detail/', InterviewEvaluationDetailAPIView.as_view(), name='interview-evaluation-detail'),
]
