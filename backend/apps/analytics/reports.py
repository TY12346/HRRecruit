"""PDF report generation helpers for analytics exports."""

from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


REPORT_TITLES = {
    'recruiter': 'Recruiter Analytics Summary',
    'interviewer': 'Interviewer Analytics Summary',
    'hr_head': 'HR Head Analytics Summary',
}

METRIC_LABELS = {
    'total_job_postings': 'Total Job Postings',
    'total_applications': 'Total Applications',
    'shortlisted_count': 'Shortlisted Candidates',
    'rejected_count': 'Rejected Candidates',
    'hired_count': 'Hired Candidates',
    'average_time_to_hire_days': 'Average Time to Hire (Days)',
    'dropout_rate': 'Candidate Dropout Rate (%)',
    'offer_acceptance_rate': 'Offer Acceptance Rate (%)',
    'total_offers': 'Total Offers',
    'accepted_offers': 'Accepted Offers',
    'recruiter_hire_count': 'Recruiter Hire Count',
    'interviewer_evaluation_count': 'Evaluation Submission Count',
    'assigned_interviews': 'Assigned Interviews',
    'completed_interviews': 'Completed Interviews',
    'average_evaluation_score': 'Average Evaluation Score',
    'hiring_success_rate': 'Hiring Success Rate (%)',
    'rejection_rate': 'Rejection Rate (%)',
}

REPORT_METRICS = {
    'recruiter': [
        'total_job_postings',
        'total_applications',
        'shortlisted_count',
        'rejected_count',
        'hired_count',
        'average_time_to_hire_days',
        'recruiter_hire_count',
        'interviewer_evaluation_count',
    ],
    'interviewer': [
        'assigned_interviews',
        'completed_interviews',
        'interviewer_evaluation_count',
        'average_evaluation_score',
        'total_applications',
        'shortlisted_count',
        'rejected_count',
        'hired_count',
    ],
    'hr_head': [
        'total_job_postings',
        'total_applications',
        'shortlisted_count',
        'rejected_count',
        'hired_count',
        'hiring_success_rate',
        'rejection_rate',
        'dropout_rate',
        'offer_acceptance_rate',
        'average_time_to_hire_days',
    ],
}


def _table(data, column_widths=None):
    table = Table(data, colWidths=column_widths, hAlign='LEFT')
    table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#d1d5db')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _format_value(value):
    if value is None:
        return '-'
    if isinstance(value, float):
        return f'{value:.2f}'
    return str(value)


def _add_heading(story, styles, text):
    story.append(Spacer(1, 12))
    story.append(Paragraph(text, styles['Heading2']))
    story.append(Spacer(1, 6))


def _append_metrics(story, report_type, metrics):
    rows = [['Metric', 'Value']]
    for key in REPORT_METRICS[report_type]:
        rows.append([METRIC_LABELS[key], _format_value(metrics.get(key))])
    story.append(_table(rows, [270, 180]))


def _append_status_counts(story, styles, metrics):
    status_counts = metrics.get('applications_by_status', {})
    if not status_counts:
        return
    _add_heading(story, styles, 'Applications by Status')
    rows = [['Status', 'Count']]
    rows.extend([[status.replace('_', ' ').title(), count] for status, count in status_counts.items()])
    story.append(_table(rows, [270, 180]))


def _append_performance_table(story, styles, title, rows, columns):
    _add_heading(story, styles, title)
    table_rows = [[label for label, _key in columns]]
    for row in rows:
        table_rows.append([_format_value(row.get(key)) for _label, key in columns])
    if len(table_rows) == 1:
        table_rows.append(['No data available'] + [''] * (len(columns) - 1))
    story.append(_table(table_rows))


def build_analytics_summary_pdf(report_type, dashboard, user):
    """Return PDF bytes for a role-specific analytics dashboard payload."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title=REPORT_TITLES[report_type],
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(REPORT_TITLES[report_type], styles['Title']), Spacer(1, 12)]

    generated_at = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M %Z')
    organization = dashboard['organization']
    story.append(
        _table(
            [
                ['Generated Date', generated_at],
                ['User', f'{user.full_name} ({user.email})'],
                ['Role', user.get_role_display()],
                ['Organization', f"{organization['name']} (ID: {organization['id']})"],
            ],
            [130, 320],
        )
    )

    _add_heading(story, styles, 'Key Metrics')
    _append_metrics(story, report_type, dashboard['metrics'])
    _append_status_counts(story, styles, dashboard['metrics'])

    if report_type == 'hr_head':
        _append_performance_table(
            story,
            styles,
            'Recruiter Performance',
            dashboard.get('recruiter_performance', []),
            [
                ('Recruiter', 'recruiter_name'),
                ('Job Postings', 'job_postings'),
                ('Applications', 'applications'),
                ('Hires', 'hire_count'),
            ],
        )
        _append_performance_table(
            story,
            styles,
            'Interviewer Performance',
            dashboard.get('interviewer_performance', []),
            [
                ('Interviewer', 'interviewer_name'),
                ('Assigned', 'assigned_interviews'),
                ('Completed', 'completed_interviews'),
                ('Evaluations', 'evaluation_count'),
                ('Avg Score', 'average_evaluation_score'),
            ],
        )

    document.build(story)
    return buffer.getvalue()
