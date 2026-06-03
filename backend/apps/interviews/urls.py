from django.urls import path

from apps.evaluations.views import (
    InterviewEvaluationDetailAPIView,
    InterviewEvaluationSubmitAPIView,
    InterviewRecordingUploadAPIView,
)
from .views import AssignedInterviewListAPIView, InterviewDetailAPIView, InterviewListAPIView, SendInterviewInvitationAPIView

urlpatterns = [
    path('', InterviewListAPIView.as_view(), name='interview-list'),
    path('assigned/', AssignedInterviewListAPIView.as_view(), name='interview-assigned-list'),
    path('<int:interview_id>/', InterviewDetailAPIView.as_view(), name='interview-detail'),
    path('<int:interview_id>/send-invitation/', SendInterviewInvitationAPIView.as_view(), name='interview-send-invitation'),
    path('<int:interview_id>/recordings/', InterviewRecordingUploadAPIView.as_view(), name='interview-recording-upload'),
    path('<int:interview_id>/evaluations/', InterviewEvaluationSubmitAPIView.as_view(), name='interview-evaluation-submit'),
    path('<int:interview_id>/evaluation-detail/', InterviewEvaluationDetailAPIView.as_view(), name='interview-evaluation-detail'),
]
