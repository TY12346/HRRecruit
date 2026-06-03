from django.urls import path

from apps.applications.views import JobApplyAPIView, RankedCandidatesAPIView

from .views import (
    JobDetailAPIView,
    JobDuplicateAPIView,
    JobEvaluationFormAPIView,
    JobListCreateAPIView,
    JobRequirementsAPIView,
    JobSaveAPIView,
    SavedJobListAPIView,
)

urlpatterns = [
    path('', JobListCreateAPIView.as_view(), name='job-list-create'),
    path('saved/', SavedJobListAPIView.as_view(), name='saved-job-list'),
    path('<int:job_id>/', JobDetailAPIView.as_view(), name='job-detail'),
    path('<int:job_id>/duplicate/', JobDuplicateAPIView.as_view(), name='job-duplicate'),
    path('<int:job_id>/requirements/', JobRequirementsAPIView.as_view(), name='job-requirements'),
    path('<int:job_id>/eval-form/', JobEvaluationFormAPIView.as_view(), name='job-evaluation-form'),
    path('<int:job_id>/save/', JobSaveAPIView.as_view(), name='job-save'),
    path('<int:job_id>/apply/', JobApplyAPIView.as_view(), name='job-apply'),
    path('<int:job_id>/ranked-candidates/', RankedCandidatesAPIView.as_view(), name='job-ranked-candidates'),
]
