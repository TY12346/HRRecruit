"""Domain checks for the job-level hiring recommendation workflow."""

from apps.applications.models import JobApplication
from apps.interviews.models import Interview
from apps.jobs.models import JobPosting


INCOMPLETE_SHORTLIST_STATUSES = {
    JobApplication.Status.SHORTLISTED,
    JobApplication.Status.INTERVIEW_INVITED,
    JobApplication.Status.INTERVIEW_ACCEPTED,
    JobApplication.Status.INTERVIEWING,
}

ELIGIBLE_RECOMMENDATION_STATUSES = {
    JobApplication.Status.EVALUATION_SUBMITTED,
    JobApplication.Status.DECISION_PENDING,
    JobApplication.Status.HR_APPROVED,
    JobApplication.Status.HR_REJECTED,
    JobApplication.Status.OFFER_SENT,
    JobApplication.Status.OFFER_ACCEPTED,
    JobApplication.Status.OFFER_DECLINED,
    JobApplication.Status.HIRED,
}


def recommendation_readiness(job):
    reasons = []
    if job.status == JobPosting.Status.OPEN:
        reasons.append('Application intake is still open.')

    applications = job.applications.all()
    incomplete = applications.filter(status__in=INCOMPLETE_SHORTLIST_STATUSES)
    if incomplete.exists():
        names = ', '.join(incomplete.values_list('applicant__full_name', flat=True)[:5])
        reasons.append(f'Shortlisted applicants still require a final interview/evaluation state: {names}.')

    completed_without_evaluation = Interview.objects.filter(
        application__job=job,
        status=Interview.Status.COMPLETED,
        evaluations__isnull=True,
    ).distinct()
    if completed_without_evaluation.exists():
        reasons.append(f'{completed_without_evaluation.count()} completed interview(s) still require an interviewer evaluation.')

    eligible_count = applications.filter(status__in=ELIGIBLE_RECOMMENDATION_STATUSES).count()
    return {
        'ready': not reasons,
        'reasons': reasons,
        'eligible_applicant_count': eligible_count,
    }


def refresh_job_readiness(job):
    readiness = recommendation_readiness(job)
    transitional = {
        JobPosting.Status.APPLICATION_INTAKE_CLOSED,
        JobPosting.Status.INTERVIEWS_IN_PROGRESS,
        JobPosting.Status.READY_FOR_RECOMMENDATION,
    }
    if job.status in transitional:
        desired = JobPosting.Status.READY_FOR_RECOMMENDATION if readiness['ready'] else JobPosting.Status.INTERVIEWS_IN_PROGRESS
        if job.status != desired:
            job.status = desired
            job.save(update_fields=['status', 'updated_at'])
    return readiness
