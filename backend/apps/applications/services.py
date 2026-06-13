"""Application workflow services."""

from django.db import transaction

from apps.ai_services.resume_screening import SCREENING_THRESHOLD, build_resume_screening

from .models import JobApplication


def screen_job_application(application, changed_by):
    """Run local resume screening, persist its result, and record the stage change."""
    screening_result = build_resume_screening(application)
    is_qualified = screening_result['final_score'] >= SCREENING_THRESHOLD
    new_status = JobApplication.Status.SCREENED_QUALIFIED if is_qualified else JobApplication.Status.REJECTED
    history_note = (
        'AI-assisted resume screening completed. Recruiter review is still required.'
        if is_qualified
        else 'AI-assisted resume screening rejected this applicant due to underqualification.'
    )

    with transaction.atomic():
        application = JobApplication.objects.select_for_update().get(pk=application.pk)
        for field, value in screening_result.items():
            setattr(application, field, value)
        application.save(update_fields=[*screening_result, 'updated_at'])
        application.change_status(
            new_status,
            changed_by=changed_by,
            note=history_note,
        )

    application.refresh_from_db()
    return application
