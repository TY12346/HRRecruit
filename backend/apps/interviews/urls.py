from django.urls import path

from .views import AssignedInterviewListAPIView, InterviewDetailAPIView, InterviewListAPIView, SendInterviewInvitationAPIView

urlpatterns = [
    path('', InterviewListAPIView.as_view(), name='interview-list'),
    path('assigned/', AssignedInterviewListAPIView.as_view(), name='interview-assigned-list'),
    path('<int:interview_id>/', InterviewDetailAPIView.as_view(), name='interview-detail'),
    path('<int:interview_id>/send-invitation/', SendInterviewInvitationAPIView.as_view(), name='interview-send-invitation'),
]
