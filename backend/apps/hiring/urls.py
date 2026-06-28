from django.urls import path

from .views import (
    HiringDecisionApproveAPIView,
    HiringDecisionDetailAPIView,
    HiringDecisionRejectAPIView,
    JobOfferAcceptAPIView,
    JobOfferDeclineAPIView,
    JobOfferListAPIView,
    JobOfferWithdrawAPIView,
    PendingHiringDecisionListAPIView,
)

urlpatterns = [
    path('hiring-decisions/pending/', PendingHiringDecisionListAPIView.as_view(), name='hiring-decision-pending-list'),
    path('hiring-decisions/<int:decision_id>/', HiringDecisionDetailAPIView.as_view(), name='hiring-decision-detail'),
    path('hiring-decisions/<int:decision_id>/approve/', HiringDecisionApproveAPIView.as_view(), name='hiring-decision-approve'),
    path('hiring-decisions/<int:decision_id>/reject/', HiringDecisionRejectAPIView.as_view(), name='hiring-decision-reject'),
    path('job-offers/', JobOfferListAPIView.as_view(), name='job-offer-list'),
    path('job-offers/<int:offer_id>/accept/', JobOfferAcceptAPIView.as_view(), name='job-offer-accept'),
    path('job-offers/<int:offer_id>/decline/', JobOfferDeclineAPIView.as_view(), name='job-offer-decline'),
    path('job-offers/<int:offer_id>/withdraw/', JobOfferWithdrawAPIView.as_view(), name='job-offer-withdraw'),
]
