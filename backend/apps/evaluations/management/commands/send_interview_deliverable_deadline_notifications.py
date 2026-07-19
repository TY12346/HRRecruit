"""Send due-soon and late notifications for missing interview deliverables."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.interviews.models import Interview
from apps.evaluations.deliverables import (
    ALMOST_LATE_NOTIFICATION_TYPE,
    LATE_NOTIFICATION_TYPE,
    create_interviewer_deadline_notification,
    deliverable_status_for,
)


class Command(BaseCommand):
    help = 'Notify interviewers when transcript, AI summary, and evaluation scorecard deliverables are almost late or late.'

    def handle(self, *args, **options):
        now = timezone.now()
        sent = 0
        interviews = Interview.objects.select_related('interviewer', 'application', 'application__applicant', 'application__job').filter(
            scheduled_datetime__isnull=False,
            interviewer__isnull=False,
        )
        for interview in interviews:
            status = deliverable_status_for(interview, at_time=now)
            if status['is_complete']:
                continue
            applicant = interview.application.applicant.full_name
            job_title = interview.application.job.title
            missing = ', '.join(status['missing'])
            deadline = timezone.localtime(status['deadline']).strftime('%Y-%m-%d %H:%M')
            if status['is_late']:
                notification = create_interviewer_deadline_notification(
                    interview,
                    LATE_NOTIFICATION_TYPE,
                    'Interview deliverables are late',
                    f'The transcript, AI summary, and evaluation scorecard for {applicant} ({job_title}) were due by {deadline}. Missing: {missing}.',
                )
            elif status['is_almost_late']:
                notification = create_interviewer_deadline_notification(
                    interview,
                    ALMOST_LATE_NOTIFICATION_TYPE,
                    'Interview deliverables due soon',
                    f'Submit the transcript, AI summary, and evaluation scorecard for {applicant} ({job_title}) by {deadline}. Missing: {missing}.',
                )
            else:
                notification = None
            if notification:
                sent += 1
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} interview deliverable deadline notification(s).'))
