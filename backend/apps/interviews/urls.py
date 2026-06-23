from django.urls import path

from apps.evaluations.views import (
    InterviewEvaluationDetailAPIView,
    InterviewEvaluationSubmitAPIView,
    InterviewRecordingUploadAPIView,
)
from .views import AssignedInterviewListAPIView, BookSchedulingRequestAPIView, InterviewDetailAPIView, InterviewListAPIView, InterviewSchedulingRequestListAPIView, InterviewerAvailabilitySlotDetailAPIView, InterviewerAvailabilitySlotListCreateAPIView

urlpatterns = [
    path('', InterviewListAPIView.as_view(), name='interview-list'),
    path('assigned/', AssignedInterviewListAPIView.as_view(), name='interview-assigned-list'),
    path('availability/', InterviewerAvailabilitySlotListCreateAPIView.as_view(), name='interviewer-availability-list-create'),
    path('availability/<int:slot_id>/', InterviewerAvailabilitySlotDetailAPIView.as_view(), name='interviewer-availability-detail'),
    path('scheduling-requests/', InterviewSchedulingRequestListAPIView.as_view(), name='interview-scheduling-request-list'),
    path('scheduling-requests/<int:scheduling_request_id>/book/', BookSchedulingRequestAPIView.as_view(), name='interview-scheduling-request-book'),
    path('<int:interview_id>/', InterviewDetailAPIView.as_view(), name='interview-detail'),
    path('<int:interview_id>/recordings/', InterviewRecordingUploadAPIView.as_view(), name='interview-recording-upload'),
    path('<int:interview_id>/evaluations/', InterviewEvaluationSubmitAPIView.as_view(), name='interview-evaluation-submit'),
    path('<int:interview_id>/evaluation-detail/', InterviewEvaluationDetailAPIView.as_view(), name='interview-evaluation-detail'),
]
