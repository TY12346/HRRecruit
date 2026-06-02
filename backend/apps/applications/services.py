"""Application workflow services."""

from django.db import transaction

from apps.ai_services.resume_screening import SCREENING_THRESHOLD, build_resume_screening

from .models import JobApplication


def schedule_resume_screening(application):
    """Placeholder for a future asynchronous AI resume-screening request."""
    # Screening is recruiter-triggered and synchronous until a background task
    # system is intentionally introduced.
    return None


def screen_job_application(application, changed_by):
    """Run local resume screening, persist its result, and record the stage change."""
    screening_result = build_resume_screening(application)
    new_status = (
        JobApplication.Status.SCREENED_QUALIFIED
        if screening_result['final_score'] >= SCREENING_THRESHOLD
        else JobApplication.Status.SCREENED_NOT_QUALIFIED
    )

    with transaction.atomic():
        application = JobApplication.objects.select_for_update().get(pk=application.pk)
        for field, value in screening_result.items():
            setattr(application, field, value)
        application.save(update_fields=[*screening_result, 'updated_at'])
        application.change_status(
            new_status,
            changed_by=changed_by,
            note='AI-assisted resume screening completed. Recruiter review is still required.',
        )

    application.refresh_from_db()
    return application
