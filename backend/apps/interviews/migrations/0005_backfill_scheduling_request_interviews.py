from django.db import migrations


def backfill_scheduling_request_interviews(apps, schema_editor):
    Interview = apps.get_model('interviews', 'Interview')
    InterviewSchedulingRequest = apps.get_model('interviews', 'InterviewSchedulingRequest')
    InterviewStatusHistory = apps.get_model('interviews', 'InterviewStatusHistory')
    JobApplication = apps.get_model('applications', 'JobApplication')

    for scheduling_request in InterviewSchedulingRequest.objects.select_related(
        'application',
        'application__job',
    ).filter(interview__isnull=True):
        application = scheduling_request.application
        interview, created = Interview.objects.get_or_create(
            application=application,
            defaults={
                'organization_id': scheduling_request.organization_id,
                'recruiter_id': scheduling_request.recruiter_id,
                'interviewer_id': scheduling_request.interviewer_id,
                'status': 'assigned',
                'scheduling_method': 'self_scheduled',
            },
        )
        update_fields = []
        if interview.organization_id != scheduling_request.organization_id:
            interview.organization_id = scheduling_request.organization_id
            update_fields.append('organization')
        if interview.recruiter_id != scheduling_request.recruiter_id:
            interview.recruiter_id = scheduling_request.recruiter_id
            update_fields.append('recruiter')
        if interview.interviewer_id != scheduling_request.interviewer_id:
            interview.interviewer_id = scheduling_request.interviewer_id
            update_fields.append('interviewer')
        if interview.scheduling_method != 'self_scheduled':
            interview.scheduling_method = 'self_scheduled'
            update_fields.append('scheduling_method')
        if update_fields:
            update_fields.append('updated_at')
            interview.save(update_fields=update_fields)
        if created:
            InterviewStatusHistory.objects.create(
                interview=interview,
                from_status='assigned',
                to_status='assigned',
                changed_by_id=scheduling_request.recruiter_id,
                note='Backfilled interview assignment for self-scheduling request.',
            )

        scheduling_request.interview = interview
        scheduling_request.save(update_fields=['interview', 'updated_at'])

        if application.assigned_interviewer_id != scheduling_request.interviewer_id:
            application.assigned_interviewer_id = scheduling_request.interviewer_id
            application.save(update_fields=['assigned_interviewer', 'updated_at'])
        if application.status not in ('withdrawn', 'rejected') and application.status != 'shortlisted':
            application.status = 'shortlisted'
            application.save(update_fields=['status', 'updated_at'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0004_alter_interviewstatushistory_options'),
        ('applications', '0004_alter_applicationstagehistory_options'),
    ]

    operations = [
        migrations.RunPython(backfill_scheduling_request_interviews, noop_reverse),
    ]
