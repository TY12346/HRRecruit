"""Analytics aggregation helpers for HRRecruit dashboards."""

from collections import OrderedDict

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncMonth
from rest_framework.exceptions import PermissionDenied

from apps.applications.models import ApplicationStageHistory, JobApplication
from apps.evaluations.models import InterviewEvaluation
from apps.hiring.models import JobOffer
from apps.interviews.models import Interview
from apps.jobs.models import JobPosting
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


DROPOUT_STATUSES = (JobApplication.Status.REJECTED,)
REJECTED_STATUSES = (JobApplication.Status.REJECTED,)
SHORTLIST_OR_BEYOND_STATUSES = (JobApplication.Status.UNDER_REVIEW,)
INTERVIEW_OR_BEYOND_STATUSES = (JobApplication.Status.UNDER_REVIEW,)
EVALUATION_OR_BEYOND_STATUSES = (JobApplication.Status.UNDER_REVIEW,)
OFFER_OR_BEYOND_STATUSES = (JobApplication.Status.UNDER_REVIEW,)

FUNNEL_STAGES = OrderedDict(
    (
        ('Under review', (JobApplication.Status.UNDER_REVIEW,)),
        ('Rejected', REJECTED_STATUSES),
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


def applicant_funnel(applications):
    status_counts = applications_by_status(applications)
    labels = list(FUNNEL_STAGES.keys())
    data = [sum(status_counts.get(status, 0) for status in statuses) for statuses in FUNNEL_STAGES.values()]
    return Chart.single_dataset(labels, data, 'Applicants')


def applicant_pipeline_sankey(applications):
    """Build mutually exclusive applicant flows for a Sankey pipeline chart."""
    total = applications.count()
    rejected = applications.filter(status=JobApplication.Status.REJECTED).count()
    under_review = applications.filter(status=JobApplication.Status.UNDER_REVIEW)
    under_review_count = under_review.count()
    # A later-stage record implies the applicant passed earlier stages, even if
    # legacy/imported data does not include every intermediate interview row.
    interviewed = under_review.filter(
        Q(interviews__isnull=False) | Q(job_offers__isnull=False),
    ).distinct()
    interviewed_count = interviewed.count()
    evaluated = interviewed.filter(
        Q(interviews__evaluations__isnull=False) | Q(job_offers__isnull=False),
    ).distinct()
    evaluated_count = evaluated.count()
    offered = evaluated.filter(job_offers__isnull=False).distinct()
    offered_count = offered.count()
    hired_count = offered.filter(
        job_offers__offer_status=JobOffer.OfferStatus.ACCEPTED,
    ).distinct().count()
    declined_count = offered.exclude(
        job_offers__offer_status=JobOffer.OfferStatus.ACCEPTED,
    ).filter(job_offers__offer_status=JobOffer.OfferStatus.REJECTED).distinct().count()
    pending_offer_count = max(offered_count - hired_count - declined_count, 0)

    nodes = [
        {'id': 'applications', 'label': 'Applications', 'column': 0, 'color': '#2563eb'},
        {'id': 'under_review', 'label': 'Under review', 'column': 1, 'color': '#3b82f6'},
        {'id': 'rejected', 'label': 'Rejected', 'column': 1, 'color': '#dc2626'},
        {'id': 'interviewed', 'label': 'Interviewed', 'column': 2, 'color': '#0ea5e9'},
        {'id': 'awaiting_interview', 'label': 'Awaiting interview', 'column': 2, 'color': '#94a3b8'},
        {'id': 'evaluated', 'label': 'Evaluated', 'column': 3, 'color': '#8b5cf6'},
        {'id': 'awaiting_evaluation', 'label': 'Awaiting evaluation', 'column': 3, 'color': '#94a3b8'},
        {'id': 'offer_sent', 'label': 'Offer sent', 'column': 4, 'color': '#f59e0b'},
        {'id': 'no_offer', 'label': 'No offer yet', 'column': 4, 'color': '#94a3b8'},
        {'id': 'hired', 'label': 'Hired', 'column': 5, 'color': '#16a34a'},
        {'id': 'offer_declined', 'label': 'Offer declined', 'column': 5, 'color': '#f97316'},
        {'id': 'offer_pending', 'label': 'Offer pending', 'column': 5, 'color': '#64748b'},
    ]
    candidate_links = [
        ('applications', 'under_review', under_review_count),
        ('applications', 'rejected', rejected),
        ('under_review', 'interviewed', interviewed_count),
        ('under_review', 'awaiting_interview', under_review_count - interviewed_count),
        ('interviewed', 'evaluated', evaluated_count),
        ('interviewed', 'awaiting_evaluation', interviewed_count - evaluated_count),
        ('evaluated', 'offer_sent', offered_count),
        ('evaluated', 'no_offer', evaluated_count - offered_count),
        ('offer_sent', 'hired', hired_count),
        ('offer_sent', 'offer_declined', declined_count),
        ('offer_sent', 'offer_pending', pending_offer_count),
    ]
    links = [
        {'source': source, 'target': target, 'value': value}
        for source, target, value in candidate_links
        if value > 0
    ]
    active_node_ids = {link[key] for link in links for key in ('source', 'target')}
    return {
        'nodes': [node for node in nodes if node['id'] in active_node_ids],
        'links': links,
        'total': total,
    }


def average_time_to_hire_days(applications):
    accepted_offers = JobOffer.objects.filter(
        application__in=applications,
        offer_status=JobOffer.OfferStatus.ACCEPTED,
    ).select_related('application')
    if not accepted_offers:
        return 0.0
    durations = [
        ((offer.responded_at or offer.sent_at) - offer.application.applied_at).total_seconds() / 86400
        for offer in accepted_offers
    ]
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
            ('interview_rate', rate(applications.filter(interviews__isnull=False).distinct().count(), total)),
            ('evaluation_rate', rate(applications.filter(interviews__status=Interview.Status.EVALUATION_SUBMITTED).distinct().count(), total)),
            ('offer_rate', rate(applications.filter(job_offers__isnull=False).distinct().count(), total)),
            ('hire_rate', rate(applications.filter(job_offers__offer_status=JobOffer.OfferStatus.ACCEPTED).distinct().count(), total)),
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


def application_status_label(value):
    """Return a display label while tolerating statuses retained in legacy history rows."""
    try:
        return JobApplication.Status(value).label
    except (TypeError, ValueError):
        return str(value or 'unknown').replace('_', ' ').strip().title()


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
            'label': f"{application_status_label(row['from_stage'])} → {application_status_label(row['to_stage'])}",
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
            'insights': ['No applicant activity yet. Publish jobs and collect applications to populate analytics.'],
        }

    bottleneck_status, bottleneck_count = max(status_counts.items(), key=lambda item: item[1])
    dropout_counts = {status: status_counts.get(status, 0) for status in (*DROPOUT_STATUSES, *REJECTED_STATUSES)}
    dropout_status, dropout_count = max(dropout_counts.items(), key=lambda item: item[1])
    rates = conversion_rates(applications)
    insights = []
    if rates['shortlist_rate'] < 40:
        insights.append('Shortlist conversion is low; review job requirements, screening thresholds, and sourcing channels.')
    if rates['interview_rate'] < 25:
        insights.append('Interview conversion is low; check recruiter follow-up speed and applicant availability.')
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
                'job_id': job.public_id,
                'job_title': job.title,
                'applications': total,
                'hires': job_applications.filter(job_offers__offer_status=JobOffer.OfferStatus.ACCEPTED).distinct().count(),
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
    return Chart.single_dataset(labels, list(values.values()), 'Applicants')


def applications_over_time_chart(applications):
    values = applications_over_time(applications)
    return Chart.single_dataset(list(values.keys()), list(values.values()), 'Applications')


def top_jobs_chart(rows):
    return Chart.single_dataset([row['job_title'] for row in rows], [row['applications'] for row in rows], 'Applications')

def base_application_metrics(jobs, applications):
    from apps.hiring.models import JobHiringDecision
    from apps.jobs.models import JobPosting
    total_applications = applications.count()
    shortlisted_count = applications.filter(status=JobApplication.Status.UNDER_REVIEW).count()
    rejected_count = applications.filter(status__in=REJECTED_STATUSES).count()
    hired_count = applications.filter(job_offers__offer_status=JobOffer.OfferStatus.ACCEPTED).distinct().count()
    dropout_count = applications.filter(status__in=DROPOUT_STATUSES).count()
    offers = JobOffer.objects.filter(application__in=applications)
    total_offers = offers.count()
    accepted_offers = offers.filter(offer_status=JobOffer.OfferStatus.ACCEPTED).count()
    declined_offers = offers.filter(offer_status=JobOffer.OfferStatus.REJECTED).count()
    decisions = JobHiringDecision.objects.filter(job_posting__in=jobs)

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
        'declined_offers': declined_offers,
        'pending_hr_approval_count': decisions.filter(status=JobHiringDecision.Status.PENDING_HR_APPROVAL).count(),
        'decision_approved_count': decisions.filter(status=JobHiringDecision.Status.APPROVED).count(),
        'decision_rejected_count': decisions.filter(status=JobHiringDecision.Status.REJECTED).count(),
        'closed_no_hire_count': jobs.filter(status=JobPosting.Status.CLOSED).count(),
        'conversion_rates': conversion_rates(applications),
        'score_distribution': score_distribution(applications),
        'applications_over_time': applications_over_time(applications),
        'stage_transition_counts': stage_transition_counts(applications),
        'pipeline_health': pipeline_health(applications),
    }


def application_charts(applications):
    return {
        'applications_by_status': status_chart(applications),
        'applicant_funnel': applicant_funnel(applications),
        'applicant_pipeline_sankey': applicant_pipeline_sankey(applications),
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
    interviews = Interview.objects.filter(Q(interviewer=user) | Q(panel_interviewers=user), organization=membership.organization).distinct()
    applications = JobApplication.objects.filter(interviews__in=interviews).distinct()
    jobs = JobPosting.objects.filter(organization=membership.organization, applications__in=applications).distinct()
    evaluations = InterviewEvaluation.objects.filter(interview__in=interviews, interviewer=user)
    metrics = base_application_metrics(jobs, applications)
    top_jobs = top_jobs_by_applications(jobs, applications)
    metrics.update(
        {
            'assigned_interviews': interviews.count(),
            'completed_interviews': interviews.filter(
                status__in=[Interview.Status.COMPLETED, Interview.Status.EVALUATION_SUBMITTED]
            ).count(),
            'interviewer_evaluation_count': evaluations.count(),
            'average_evaluation_score': round(float(evaluations.aggregate(value=Avg('total_score'))['value'] or 0), 2),
        }
    )
    return {
        'dashboard': 'interviewer',
        'organization': {'id': membership.organization_id, 'name': membership.organization.name},
        'metrics': metrics,
        'charts': {**application_charts(applications), 'top_jobs_by_applications': top_jobs_chart(top_jobs)},
        'top_jobs_by_applications': top_jobs,
    }


def hiring_manager_dashboard(user):
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
                'recruiter_id': recruiter.public_id,
                'recruiter_name': recruiter.full_name,
                'job_postings': jobs.count(),
                'applications': applications.count(),
                'hire_count': applications.filter(job_offers__offer_status=JobOffer.OfferStatus.ACCEPTED).distinct().count(),
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
        interviews = Interview.objects.filter(Q(interviewer=interviewer) | Q(panel_interviewers=interviewer), organization=organization).distinct()
        evaluations = InterviewEvaluation.objects.filter(interview__in=interviews, interviewer=interviewer)
        rows.append(
            {
                'interviewer_id': interviewer.public_id,
                'interviewer_name': interviewer.full_name,
                'assigned_interviews': interviews.count(),
                'completed_interviews': interviews.filter(
                    status__in=[Interview.Status.COMPLETED, Interview.Status.EVALUATION_SUBMITTED]
                ).count(),
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
    job_filter = {'public_id': job_id, 'organization': membership.organization}
    if user.role == User.Role.RECRUITER:
        job_filter['recruiter'] = user
    if user.role == User.Role.INTERVIEWER:
        job_filter['applications__interviews__interviewer'] = user
    job = JobPosting.objects.filter(**job_filter).distinct().first()
    if not job:
        raise PermissionDenied('You cannot access analytics for this job.')
    applications = JobApplication.objects.filter(job=job)
    if user.role == User.Role.INTERVIEWER:
        applications = applications.filter(interviews__interviewer=user).distinct()
    return {
        'job': {'id': job.public_id, 'title': job.title},
        'organization': {'id': membership.organization.public_id, 'name': membership.organization.name},
        'metrics': base_application_metrics(JobPosting.objects.filter(public_id=job.public_id), applications),
        'charts': application_charts(applications),
    }


def organization_overview(user):
    membership = require_analytics_membership(user, (User.Role.HR_HEAD,))
    dashboard = hiring_manager_dashboard(user)
    dashboard['dashboard'] = 'organization_overview'
    return dashboard
