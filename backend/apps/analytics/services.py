"""Analytics aggregation helpers for HRRecruit dashboards."""

from collections import OrderedDict

from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from rest_framework.exceptions import PermissionDenied

from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.evaluations.models import InterviewEvaluation
from apps.hiring.models import JobOffer
from apps.interviews.models import Interview
from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


DROPOUT_STATUSES = (
    JobApplication.Status.WITHDRAWN,
    JobApplication.Status.INTERVIEW_DECLINED,
    JobApplication.Status.OFFER_DECLINED,
)

REJECTED_STATUSES = (
    JobApplication.Status.REJECTED,
    JobApplication.Status.HR_REJECTED,
    JobApplication.Status.SCREENED_NOT_QUALIFIED,
)

SHORTLIST_OR_BEYOND_STATUSES = (
    JobApplication.Status.SHORTLISTED,
    JobApplication.Status.INTERVIEW_INVITED,
    JobApplication.Status.INTERVIEW_ACCEPTED,
    JobApplication.Status.INTERVIEW_DECLINED,
    JobApplication.Status.INTERVIEWING,
    JobApplication.Status.EVALUATION_SUBMITTED,
    JobApplication.Status.DECISION_PENDING,
    JobApplication.Status.HR_APPROVED,
    JobApplication.Status.OFFER_SENT,
    JobApplication.Status.OFFER_ACCEPTED,
    JobApplication.Status.OFFER_DECLINED,
    JobApplication.Status.HIRED,
)

INTERVIEW_OR_BEYOND_STATUSES = (
    JobApplication.Status.INTERVIEW_INVITED,
    JobApplication.Status.INTERVIEW_ACCEPTED,
    JobApplication.Status.INTERVIEW_DECLINED,
    JobApplication.Status.INTERVIEWING,
    JobApplication.Status.EVALUATION_SUBMITTED,
    JobApplication.Status.DECISION_PENDING,
    JobApplication.Status.HR_APPROVED,
    JobApplication.Status.OFFER_SENT,
    JobApplication.Status.OFFER_ACCEPTED,
    JobApplication.Status.OFFER_DECLINED,
    JobApplication.Status.HIRED,
)

EVALUATION_OR_BEYOND_STATUSES = (
    JobApplication.Status.EVALUATION_SUBMITTED,
    JobApplication.Status.DECISION_PENDING,
    JobApplication.Status.HR_APPROVED,
    JobApplication.Status.OFFER_SENT,
    JobApplication.Status.OFFER_ACCEPTED,
    JobApplication.Status.OFFER_DECLINED,
    JobApplication.Status.HIRED,
)

OFFER_OR_BEYOND_STATUSES = (
    JobApplication.Status.OFFER_SENT,
    JobApplication.Status.OFFER_ACCEPTED,
    JobApplication.Status.OFFER_DECLINED,
    JobApplication.Status.HIRED,
)

FUNNEL_STAGES = OrderedDict(
    (
        ('Applied', (JobApplication.Status.SUBMITTED,)),
        (
            'Screened',
            (
                JobApplication.Status.SCREENED,
                JobApplication.Status.SCREENED_QUALIFIED,
                JobApplication.Status.SCREENED_NOT_QUALIFIED,
            ),
        ),
        ('Shortlisted', (JobApplication.Status.SHORTLISTED,)),
        (
            'Interview',
            (
                JobApplication.Status.INTERVIEW_INVITED,
                JobApplication.Status.INTERVIEW_ACCEPTED,
                JobApplication.Status.INTERVIEW_DECLINED,
                JobApplication.Status.INTERVIEWING,
            ),
        ),
        ('Evaluated', (JobApplication.Status.EVALUATION_SUBMITTED,)),
        ('Decision Pending', (JobApplication.Status.DECISION_PENDING,)),
        (
            'HR Review',
            (
                JobApplication.Status.HR_APPROVED,
                JobApplication.Status.HR_REJECTED,
            ),
        ),
        (
            'Offer',
            (
                JobApplication.Status.OFFER_SENT,
                JobApplication.Status.OFFER_ACCEPTED,
                JobApplication.Status.OFFER_DECLINED,
            ),
        ),
        ('Hired', (JobApplication.Status.HIRED,)),
        ('Rejected', REJECTED_STATUSES),
        ('Dropped Out', DROPOUT_STATUSES),
    )
)


class Chart:
    COLORS = [
        '#2563eb',
        '#16a34a',
        '#f97316',
        '#dc2626',
        '#7c3aed',
        '#0891b2',
        '#ca8a04',
        '#be123c',
        '#4b5563',
        '#0f766e',
        '#9333ea',
    ]

    @staticmethod
    def dataset(label, data, background_colors=None):
        payload = {'label': label, 'data': data}
        if background_colors:
            payload['backgroundColor'] = background_colors
        return payload

    @classmethod
    def single_dataset(cls, labels, data, label='Count'):
        colors = [cls.COLORS[index % len(cls.COLORS)] for index in range(len(labels))]
        return {
            'labels': labels,
            'datasets': [cls.dataset(label, data, colors)],
        }


def active_membership_for(user, roles=None):
    filters = {
        'user': user,
        'status': OrganizationMembership.Status.ACTIVE,
        'organization__status': Organization.Status.ACTIVE,
    }
    if roles:
        filters['role__in'] = roles
    return OrganizationMembership.objects.filter(**filters).select_related('organization').first()


def require_analytics_membership(user, roles=None):
    if not user.is_authenticated:
        raise PermissionDenied('Authentication is required.')
    if user.role == User.Role.APPLICANT:
        raise PermissionDenied('Applicants cannot access analytics.')
    allowed_roles = roles or (User.Role.RECRUITER, User.Role.INTERVIEWER, User.Role.HR_HEAD)
    if user.role not in allowed_roles:
        raise PermissionDenied('Your role cannot access this analytics endpoint.')
    membership = active_membership_for(user, allowed_roles)
    if not membership:
        raise PermissionDenied('An active organization membership is required for analytics.')
    return membership


def applications_by_status(applications):
    raw_counts = dict(applications.values_list('status').annotate(total=Count('id')))
    return {status: raw_counts.get(status, 0) for status in JobApplication.Status.values}


def status_chart(applications):
    status_counts = applications_by_status(applications)
    labels = [choice.label for choice in JobApplication.Status]
    data = [status_counts[choice.value] for choice in JobApplication.Status]
    return Chart.single_dataset(labels, data, 'Applications')


def candidate_funnel(applications):
    status_counts = applications_by_status(applications)
    labels = list(FUNNEL_STAGES.keys())
    data = [sum(status_counts.get(status, 0) for status in statuses) for statuses in FUNNEL_STAGES.values()]
    return Chart.single_dataset(labels, data, 'Candidates')


def average_time_to_hire_days(applications):
    hired_applications = applications.filter(status=JobApplication.Status.HIRED).only('id', 'applied_at', 'updated_at')
    hired_ids = list(hired_applications.values_list('id', flat=True))
    if not hired_ids:
        return 0.0

    hired_history = {
        history['application_id']: history['changed_at']
        for history in ApplicationStageHistory.objects.filter(
            application_id__in=hired_ids,
            to_stage=JobApplication.Status.HIRED,
        )
        .order_by('application_id', 'changed_at')
        .values('application_id', 'changed_at')
    }
    durations = []
    for application in hired_applications:
        hired_at = hired_history.get(application.id) or application.updated_at
        durations.append((hired_at - application.applied_at).total_seconds() / 86400)
    return round(sum(durations) / len(durations), 2)


def rate(numerator, denominator):
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 2)



def conversion_rates(applications):
    total = applications.count()
    return OrderedDict(
        (
            ('shortlist_rate', rate(applications.filter(status__in=SHORTLIST_OR_BEYOND_STATUSES).count(), total)),
            ('interview_rate', rate(applications.filter(status__in=INTERVIEW_OR_BEYOND_STATUSES).count(), total)),
            ('evaluation_rate', rate(applications.filter(status__in=EVALUATION_OR_BEYOND_STATUSES).count(), total)),
            ('offer_rate', rate(applications.filter(status__in=OFFER_OR_BEYOND_STATUSES).count(), total)),
            ('hire_rate', rate(applications.filter(status=JobApplication.Status.HIRED).count(), total)),
        )
    )


def score_distribution(applications):
    distribution = OrderedDict((('strong_fit', 0), ('possible_fit', 0), ('low_fit', 0), ('unscored', 0)))
    for score in applications.values_list('final_score', flat=True):
        if score is None:
            distribution['unscored'] += 1
        elif float(score) >= 75:
            distribution['strong_fit'] += 1
        elif float(score) >= 50:
            distribution['possible_fit'] += 1
        else:
            distribution['low_fit'] += 1
    return distribution


def applications_over_time(applications):
    rows = (
        applications.annotate(month=TruncMonth('applied_at'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    return OrderedDict((row['month'].strftime('%b %Y') if row['month'] else 'Unknown', row['total']) for row in rows)


def stage_transition_counts(applications):
    rows = (
        ApplicationStageHistory.objects.filter(application__in=applications)
        .values('from_stage', 'to_stage')
        .annotate(total=Count('id'))
        .order_by('-total', 'from_stage', 'to_stage')[:8]
    )
    return [
        {
            'from_stage': row['from_stage'],
            'to_stage': row['to_stage'],
            'label': f"{JobApplication.Status(row['from_stage']).label} → {JobApplication.Status(row['to_stage']).label}",
            'count': row['total'],
        }
        for row in rows
    ]


def pipeline_health(applications):
    status_counts = applications_by_status(applications)
    total = sum(status_counts.values())
    if not total:
        return {
            'bottleneck_stage': None,
            'bottleneck_count': 0,
            'highest_dropout_status': None,
            'highest_dropout_count': 0,
            'insights': ['No candidate activity yet. Publish jobs and collect applications to populate analytics.'],
        }

    bottleneck_status, bottleneck_count = max(status_counts.items(), key=lambda item: item[1])
    dropout_counts = {status: status_counts.get(status, 0) for status in (*DROPOUT_STATUSES, *REJECTED_STATUSES)}
    dropout_status, dropout_count = max(dropout_counts.items(), key=lambda item: item[1])
    rates = conversion_rates(applications)
    insights = []
    if rates['shortlist_rate'] < 40:
        insights.append('Shortlist conversion is low; review job requirements, screening thresholds, and sourcing channels.')
    if rates['interview_rate'] < 25:
        insights.append('Interview conversion is low; check recruiter follow-up speed and candidate availability.')
    if rates['offer_rate'] > 0 and rates['hire_rate'] < rates['offer_rate']:
        insights.append('Offer-to-hire drop-off exists; compare compensation, response deadlines, and offer communication.')
    if not insights:
        insights.append('Pipeline movement looks healthy based on current conversion rates.')
    return {
        'bottleneck_stage': JobApplication.Status(bottleneck_status).label,
        'bottleneck_count': bottleneck_count,
        'highest_dropout_status': JobApplication.Status(dropout_status).label if dropout_status else None,
        'highest_dropout_count': dropout_count,
        'insights': insights,
    }


def top_jobs_by_applications(jobs, applications, limit=5):
    rows = []
    for job in jobs:
        job_applications = applications.filter(job=job)
        total = job_applications.count()
        rows.append(
            {
                'job_id': job.id,
                'job_title': job.title,
                'applications': total,
                'hires': job_applications.filter(status=JobApplication.Status.HIRED).count(),
                'average_score': round(float(job_applications.aggregate(value=Avg('final_score'))['value'] or 0), 2),
            }
        )
    return sorted(rows, key=lambda row: (row['applications'], row['hires']), reverse=True)[:limit]


def conversion_rates_chart(applications):
    values = conversion_rates(applications)
    labels = ['Shortlist', 'Interview', 'Evaluation', 'Offer', 'Hire']
    return Chart.single_dataset(labels, list(values.values()), 'Conversion %')


def score_distribution_chart(applications):
    values = score_distribution(applications)
    labels = ['Strong fit', 'Possible fit', 'Low fit', 'Unscored']
    return Chart.single_dataset(labels, list(values.values()), 'Candidates')


def applications_over_time_chart(applications):
    values = applications_over_time(applications)
    return Chart.single_dataset(list(values.keys()), list(values.values()), 'Applications')


def top_jobs_chart(rows):
    return Chart.single_dataset([row['job_title'] for row in rows], [row['applications'] for row in rows], 'Applications')

def base_application_metrics(jobs, applications):
    total_applications = applications.count()
    shortlisted_count = applications.filter(status=JobApplication.Status.SHORTLISTED).count()
    rejected_count = applications.filter(status__in=REJECTED_STATUSES).count()
    hired_count = applications.filter(status=JobApplication.Status.HIRED).count()
    dropout_count = applications.filter(status__in=DROPOUT_STATUSES).count()
    offers = JobOffer.objects.filter(application__in=applications)
    total_offers = offers.count()
    accepted_offers = offers.filter(offer_status=JobOffer.OfferStatus.ACCEPTED).count()

    return {
        'total_job_postings': jobs.count(),
        'total_applications': total_applications,
        'applications_by_status': applications_by_status(applications),
        'shortlisted_count': shortlisted_count,
        'rejected_count': rejected_count,
        'hired_count': hired_count,
        'average_time_to_hire_days': average_time_to_hire_days(applications),
        'dropout_rate': rate(dropout_count, total_applications),
        'offer_acceptance_rate': rate(accepted_offers, total_offers),
        'total_offers': total_offers,
        'accepted_offers': accepted_offers,
        'conversion_rates': conversion_rates(applications),
        'score_distribution': score_distribution(applications),
        'applications_over_time': applications_over_time(applications),
        'stage_transition_counts': stage_transition_counts(applications),
        'pipeline_health': pipeline_health(applications),
    }


def application_charts(applications):
    return {
        'applications_by_status': status_chart(applications),
        'candidate_funnel': candidate_funnel(applications),
        'conversion_rates': conversion_rates_chart(applications),
        'score_distribution': score_distribution_chart(applications),
        'applications_over_time': applications_over_time_chart(applications),
    }


def recruiter_dashboard(user):
    membership = require_analytics_membership(user, (User.Role.RECRUITER,))
    jobs = JobPosting.objects.filter(organization=membership.organization, recruiter=user)
    applications = JobApplication.objects.filter(job__in=jobs)
    metrics = base_application_metrics(jobs, applications)
    top_jobs = top_jobs_by_applications(jobs, applications)
    metrics['recruiter_hire_count'] = metrics['hired_count']
    metrics['interviewer_evaluation_count'] = InterviewEvaluation.objects.filter(
        interview__application__job__in=jobs,
    ).count()
    return {
        'dashboard': 'recruiter',
        'organization': {'id': membership.organization_id, 'name': membership.organization.name},
        'metrics': metrics,
        'charts': {**application_charts(applications), 'top_jobs_by_applications': top_jobs_chart(top_jobs)},
        'top_jobs_by_applications': top_jobs,
    }


def interviewer_dashboard(user):
    membership = require_analytics_membership(user, (User.Role.INTERVIEWER,))
    interviews = Interview.objects.filter(organization=membership.organization, interviewer=user)
    applications = JobApplication.objects.filter(interviews__in=interviews).distinct()
    jobs = JobPosting.objects.filter(organization=membership.organization, applications__in=applications).distinct()
    evaluations = InterviewEvaluation.objects.filter(interview__in=interviews, interviewer=user)
    metrics = base_application_metrics(jobs, applications)
    metrics.update(
        {
            'assigned_interviews': interviews.count(),
            'completed_interviews': interviews.filter(status=Interview.Status.COMPLETED).count(),
            'interviewer_evaluation_count': evaluations.count(),
            'average_evaluation_score': round(float(evaluations.aggregate(value=Avg('total_score'))['value'] or 0), 2),
        }
    )
    return {
        'dashboard': 'interviewer',
        'organization': {'id': membership.organization_id, 'name': membership.organization.name},
        'metrics': metrics,
        'charts': application_charts(applications),
    }


def hr_head_dashboard(user):
    membership = require_analytics_membership(user, (User.Role.HR_HEAD,))
    jobs = JobPosting.objects.filter(organization=membership.organization)
    applications = JobApplication.objects.filter(job__in=jobs)
    metrics = base_application_metrics(jobs, applications)
    top_jobs = top_jobs_by_applications(jobs, applications)
    metrics['hiring_success_rate'] = rate(metrics['hired_count'], metrics['total_applications'])
    metrics['rejection_rate'] = rate(metrics['rejected_count'], metrics['total_applications'])
    metrics['interviewer_evaluation_count'] = InterviewEvaluation.objects.filter(
        interview__organization=membership.organization,
    ).count()
    metrics['recruiter_hire_count'] = metrics['hired_count']
    return {
        'dashboard': 'hr_head',
        'organization': {'id': membership.organization_id, 'name': membership.organization.name},
        'metrics': metrics,
        'charts': {
            **application_charts(applications),
            'recruiter_performance': recruiter_performance_chart(membership.organization),
            'interviewer_performance': interviewer_performance_chart(membership.organization),
            'top_jobs_by_applications': top_jobs_chart(top_jobs),
        },
        'top_jobs_by_applications': top_jobs,
        'recruiter_performance': recruiter_performance(membership.organization),
        'interviewer_performance': interviewer_performance(membership.organization),
    }


def recruiter_performance(organization):
    recruiters = User.objects.filter(
        organization_memberships__organization=organization,
        organization_memberships__role=OrganizationMembership.Role.RECRUITER,
        organization_memberships__status=OrganizationMembership.Status.ACTIVE,
    ).distinct()
    rows = []
    for recruiter in recruiters:
        jobs = JobPosting.objects.filter(organization=organization, recruiter=recruiter)
        applications = JobApplication.objects.filter(job__in=jobs)
        rows.append(
            {
                'recruiter_id': recruiter.id,
                'recruiter_name': recruiter.full_name,
                'job_postings': jobs.count(),
                'applications': applications.count(),
                'hire_count': applications.filter(status=JobApplication.Status.HIRED).count(),
            }
        )
    return rows


def recruiter_performance_chart(organization):
    rows = recruiter_performance(organization)
    return {
        'labels': [row['recruiter_name'] for row in rows],
        'datasets': [
            Chart.dataset('Job Postings', [row['job_postings'] for row in rows], ['#2563eb'] * len(rows)),
            Chart.dataset('Applications', [row['applications'] for row in rows], ['#16a34a'] * len(rows)),
            Chart.dataset('Hires', [row['hire_count'] for row in rows], ['#f97316'] * len(rows)),
        ],
    }


def interviewer_performance(organization):
    interviewers = User.objects.filter(
        organization_memberships__organization=organization,
        organization_memberships__role=OrganizationMembership.Role.INTERVIEWER,
        organization_memberships__status=OrganizationMembership.Status.ACTIVE,
    ).distinct()
    rows = []
    for interviewer in interviewers:
        interviews = Interview.objects.filter(organization=organization, interviewer=interviewer)
        evaluations = InterviewEvaluation.objects.filter(interview__in=interviews, interviewer=interviewer)
        rows.append(
            {
                'interviewer_id': interviewer.id,
                'interviewer_name': interviewer.full_name,
                'assigned_interviews': interviews.count(),
                'completed_interviews': interviews.filter(status=Interview.Status.COMPLETED).count(),
                'evaluation_count': evaluations.count(),
                'average_evaluation_score': round(float(evaluations.aggregate(value=Avg('total_score'))['value'] or 0), 2),
            }
        )
    return rows


def interviewer_performance_chart(organization):
    rows = interviewer_performance(organization)
    return {
        'labels': [row['interviewer_name'] for row in rows],
        'datasets': [
            Chart.dataset('Assigned Interviews', [row['assigned_interviews'] for row in rows], ['#2563eb'] * len(rows)),
            Chart.dataset('Completed Interviews', [row['completed_interviews'] for row in rows], ['#16a34a'] * len(rows)),
            Chart.dataset('Evaluations', [row['evaluation_count'] for row in rows], ['#f97316'] * len(rows)),
        ],
    }


def job_funnel(user, job_id):
    membership = require_analytics_membership(user)
    job_filter = {'id': job_id, 'organization': membership.organization}
    if user.role == User.Role.INTERVIEWER:
        job_filter['applications__interviews__interviewer'] = user
    job = JobPosting.objects.filter(**job_filter).distinct().first()
    if not job:
        raise PermissionDenied('You cannot access analytics for this job.')
    applications = JobApplication.objects.filter(job=job)
    if user.role == User.Role.INTERVIEWER:
        applications = applications.filter(interviews__interviewer=user).distinct()
    return {
        'job': {'id': job.id, 'title': job.title},
        'organization': {'id': membership.organization_id, 'name': membership.organization.name},
        'metrics': base_application_metrics(JobPosting.objects.filter(id=job.id), applications),
        'charts': application_charts(applications),
    }


def organization_overview(user):
    membership = require_analytics_membership(user, (User.Role.HR_HEAD,))
    dashboard = hr_head_dashboard(user)
    dashboard['dashboard'] = 'organization_overview'
    return dashboard
