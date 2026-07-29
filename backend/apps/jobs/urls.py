from django.urls import path

from apps.applications.views import JobApplyAPIView, RankedApplicantsAPIView

from .views import (
    JobDetailAPIView,
    JobCloseIntakeAPIView,
    JobDuplicateAPIView,
    JobEvaluationFormAPIView,
    JobListCreateAPIView,
    JobRequisitionApproveAPIView,
    JobRequisitionCancelAPIView,
    JobRequisitionDetailAPIView,
    JobRequisitionListCreateAPIView,
    JobRequisitionRejectAPIView,
    JobRequirementsAPIView,
    JobSaveAPIView,
    SavedJobListAPIView,
)

urlpatterns = [
    path('', JobListCreateAPIView.as_view(), name='job-list-create'),
    path('saved/', SavedJobListAPIView.as_view(), name='saved-job-list'),
    path('requisitions/', JobRequisitionListCreateAPIView.as_view(), name='job-requisition-list-create'),
    path('requisitions/<str:requisition_id>/', JobRequisitionDetailAPIView.as_view(), name='job-requisition-detail'),
    path('requisitions/<str:requisition_id>/cancel/', JobRequisitionCancelAPIView.as_view(), name='job-requisition-cancel'),
    path('requisitions/<str:requisition_id>/approve/', JobRequisitionApproveAPIView.as_view(), name='job-requisition-approve'),
    path('requisitions/<str:requisition_id>/reject/', JobRequisitionRejectAPIView.as_view(), name='job-requisition-reject'),
    path('<str:job_id>/', JobDetailAPIView.as_view(), name='job-detail'),
    path('<str:job_id>/close-intake/', JobCloseIntakeAPIView.as_view(), name='job-close-intake'),
    path('<str:job_id>/duplicate/', JobDuplicateAPIView.as_view(), name='job-duplicate'),
    path('<str:job_id>/requirements/', JobRequirementsAPIView.as_view(), name='job-requirements'),
    path('<str:job_id>/scorecard/', JobEvaluationFormAPIView.as_view(), name='job-evaluation-scorecard'),
    path('<str:job_id>/eval-form/', JobEvaluationFormAPIView.as_view(), name='job-evaluation-form'),
    path('<str:job_id>/save/', JobSaveAPIView.as_view(), name='job-save'),
    path('<str:job_id>/apply/', JobApplyAPIView.as_view(), name='job-apply'),
    path('<str:job_id>/ranked-applicants/', RankedApplicantsAPIView.as_view(), name='job-ranked-applicants'),
]
