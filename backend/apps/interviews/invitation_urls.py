from django.urls import path

from .views import AcceptInterviewInvitationAPIView, DeclineInterviewInvitationAPIView, InterviewInvitationListAPIView

urlpatterns = [
    path('', InterviewInvitationListAPIView.as_view(), name='interview-invitation-list'),
    path('<int:invitation_id>/accept/', AcceptInterviewInvitationAPIView.as_view(), name='interview-invitation-accept'),
    path('<int:invitation_id>/decline/', DeclineInterviewInvitationAPIView.as_view(), name='interview-invitation-decline'),
]
