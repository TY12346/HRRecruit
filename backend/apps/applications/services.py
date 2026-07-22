"""Application workflow services."""

from django.db import transaction

from apps.ai_services.resume_screening import SCREENING_THRESHOLD, build_resume_screening
from apps.ai_services.resume_validation import ResumeContentValidationError

from .models import JobApplication


def screen_job_application(application, changed_by):
    """Run local resume screening, persist its result, and record the stage change."""
    try:
        screening_result = build_resume_screening(application)
    except ResumeContentValidationError as exc:
        with transaction.atomic():
            application = JobApplication.objects.select_for_update().get(pk=application.pk)
            application.resume_validation_result = exc.validation_result
            application.semantic_score = None
            application.skill_score = None
            application.experience_score = None
            application.education_score = None
            application.final_score = None
            application.score_explanation = {}
            application.save(update_fields=[
                'resume_validation_result', 'semantic_score', 'skill_score', 'experience_score',
                'education_score', 'final_score', 'score_explanation', 'updated_at',
            ])
        raise
    is_qualified = screening_result['final_score'] >= SCREENING_THRESHOLD
    screening_result['score_explanation']['qualification_decision'] = (
        'qualified' if is_qualified else 'not_qualified'
    )
    new_status = (
        JobApplication.Status.SCREENED_QUALIFIED
        if is_qualified
        else JobApplication.Status.SCREENED_NOT_QUALIFIED
    )
    history_note = (
        'AI-assisted resume screening completed. Recruiter review is still required.'
        if is_qualified
        else 'AI-assisted resume screening found this applicant not qualified; recruiter review remains available.'
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
