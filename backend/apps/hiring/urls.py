from django.urls import path

from .views import (
    HiringDecisionApproveAPIView,
    HiringDecisionDetailAPIView,
    HiringDecisionRejectAPIView,
    JobOfferAcceptAPIView,
    JobOfferApproveAPIView,
    JobOfferDisapproveAPIView,
    JobOfferDeclineAPIView,
    JobOfferListAPIView,
    JobOfferWithdrawAPIView,
    JobOfferResubmitAPIView,
    JobOfferSendAPIView,
    PendingHiringDecisionListAPIView,
    JobApplicantComparisonAPIView,
    JobHiringDecisionListCreateAPIView,
    JobHiringDecisionApproveAPIView,
    JobHiringDecisionRejectAPIView,
)

urlpatterns = [
    path('jobs/<str:job_id>/applicant-comparison/', JobApplicantComparisonAPIView.as_view(), name='job-applicant-comparison'),
    path('job-hiring-decisions/', JobHiringDecisionListCreateAPIView.as_view(), name='job-hiring-decision-list-create'),
    path('job-hiring-decisions/<str:decision_id>/approve/', JobHiringDecisionApproveAPIView.as_view(), name='job-hiring-decision-approve'),
    path('job-hiring-decisions/<str:decision_id>/reject/', JobHiringDecisionRejectAPIView.as_view(), name='job-hiring-decision-reject'),
    path('hiring-decisions/pending/', PendingHiringDecisionListAPIView.as_view(), name='hiring-decision-pending-list'),
    path('hiring-decisions/<str:decision_id>/', HiringDecisionDetailAPIView.as_view(), name='hiring-decision-detail'),
    path('hiring-decisions/<str:decision_id>/approve/', HiringDecisionApproveAPIView.as_view(), name='hiring-decision-approve'),
    path('hiring-decisions/<str:decision_id>/reject/', HiringDecisionRejectAPIView.as_view(), name='hiring-decision-reject'),
    path('job-offers/', JobOfferListAPIView.as_view(), name='job-offer-list'),
    path('job-offers/<str:offer_id>/accept/', JobOfferAcceptAPIView.as_view(), name='job-offer-accept'),
    path('job-offers/<str:offer_id>/decline/', JobOfferDeclineAPIView.as_view(), name='job-offer-decline'),
    path('job-offers/<str:offer_id>/approve/', JobOfferApproveAPIView.as_view(), name='job-offer-approve'),
    path('job-offers/<str:offer_id>/disapprove/', JobOfferDisapproveAPIView.as_view(), name='job-offer-disapprove'),
    path('job-offers/<str:offer_id>/resubmit/', JobOfferResubmitAPIView.as_view(), name='job-offer-resubmit'),
    path('job-offers/<str:offer_id>/send/', JobOfferSendAPIView.as_view(), name='job-offer-send'),
    path('job-offers/<str:offer_id>/withdraw/', JobOfferWithdrawAPIView.as_view(), name='job-offer-withdraw'),
]
