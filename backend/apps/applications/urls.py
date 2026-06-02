from django.urls import path

from .views import (
    ApplicationDetailAPIView,
    ApplicationListAPIView,
    ApplicationScreenAPIView,
    ApplicationStatusHistoryAPIView,
)

urlpatterns = [
    path('', ApplicationListAPIView.as_view(), name='application-list'),
    path('<int:application_id>/', ApplicationDetailAPIView.as_view(), name='application-detail'),
    path('<int:application_id>/screen/', ApplicationScreenAPIView.as_view(), name='application-screen'),
    path('<int:application_id>/status-history/', ApplicationStatusHistoryAPIView.as_view(), name='application-status-history'),
]
