"""Application workflow services."""

from django.db import transaction

from apps.ai_services.resume_screening import SCREENING_THRESHOLD, build_resume_screening

from .models import JobApplication


def screen_job_application(application):
    """Run local resume screening and persist its extracted data and scores."""
    screening_result = build_resume_screening(application)
    is_qualified = screening_result['final_score'] >= SCREENING_THRESHOLD
    screening_result['score_explanation']['qualification_decision'] = (
        'qualified' if is_qualified else 'not_qualified'
    )
    screened_status = (
        JobApplication.Status.SHORTLISTED
        if is_qualified
        else JobApplication.Status.REJECTED
    )
    with transaction.atomic():
        application = JobApplication.objects.select_for_update().get(pk=application.pk)
        for field, value in screening_result.items():
            setattr(application, field, value)
        application.save(update_fields=[*screening_result, 'updated_at'])
        application.change_status(
            screened_status,
            note='AI resume screening completed; the recruiter retains the final decision.',
        )

    application.refresh_from_db()
    return application
