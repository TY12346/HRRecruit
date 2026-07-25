"""Domain checks for the job-level hiring decision workflow."""

from apps.applications.models import JobApplication
from apps.interviews.models import Interview
from apps.jobs.models import JobPosting


ELIGIBLE_DECISION_STATUSES = {JobApplication.Status.UNDER_REVIEW}


def interview_scorecard_progress(interview):
    """Return the submitted/required scorecard count for an interview.

    The primary interviewer is not stored in ``panel_interviewers``, so both
    sources must be considered.  Keeping this calculation in one place avoids
    treating the first panel scorecard as a completed evaluation.
    """
    assigned_interviewer_ids = set(interview.panel_interviewers.values_list('id', flat=True))
    if interview.interviewer_id:
        assigned_interviewer_ids.add(interview.interviewer_id)
    submitted_interviewer_ids = set(interview.evaluations.values_list('interviewer_id', flat=True))
    return len(submitted_interviewer_ids & assigned_interviewer_ids), len(assigned_interviewer_ids)


def application_scorecard_progress(application):
    """Return scorecard progress and whether all completed interviews are ready."""
    interviews = list(application.interviews.filter(status=Interview.Status.EVALUATION_SUBMITTED).prefetch_related(
        'panel_interviewers', 'evaluations'
    ))
    submitted = required = 0
    complete = True
    for interview in interviews:
        interview_submitted, interview_required = interview_scorecard_progress(interview)
        submitted += interview_submitted
        required += interview_required
        if not interview_required or interview_submitted < interview_required:
            complete = False
    return {
        'submitted': submitted,
        'required': required,
        'complete': complete,
        'has_completed_interviews': bool(interviews),
    }


def decision_readiness(job):
    applications = job.applications.filter(status__in=ELIGIBLE_DECISION_STATUSES).prefetch_related(
        'interviews__panel_interviewers', 'interviews__evaluations'
    )
    eligible_count = sum(
        application_scorecard_progress(application)['complete']
        for application in applications
    )
    reasons = [] if eligible_count else ['At least one applicant must be available for hiring.']
    return {
        'ready': eligible_count > 0,
        'reasons': reasons,
        'eligible_applicant_count': eligible_count,
    }


def refresh_job_readiness(job):
    readiness = decision_readiness(job)
    transitional = {
        JobPosting.Status.CLOSED,
        JobPosting.Status.CLOSED,
        JobPosting.Status.CLOSED,
    }
    if job.status in transitional:
        desired = JobPosting.Status.CLOSED if readiness['ready'] else JobPosting.Status.CLOSED
        if job.status != desired:
            job.status = desired
            job.save(update_fields=['status', 'updated_at'])
    return readiness
