from django.urls import path

from .views import (
    ApplicationDetailAPIView,
    ApplicationListAPIView,
    ApplicationRejectAPIView,
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
    path('<int:application_id>/shortlist/', ApplicationShortlistAPIView.as_view(), name='application-shortlist'),
    path('<int:application_id>/reject/', ApplicationRejectAPIView.as_view(), name='application-reject'),
    path('<int:application_id>/remark/', ApplicationRemarkAPIView.as_view(), name='application-remark'),
    path('<int:application_id>/status-history/', ApplicationStatusHistoryAPIView.as_view(), name='application-status-history'),
]
