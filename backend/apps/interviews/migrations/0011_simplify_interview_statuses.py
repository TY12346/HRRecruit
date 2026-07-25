from django.db import migrations, models
from django.db.models import Q


def map_interview_statuses(apps, schema_editor):
    Interview = apps.get_model('interviews', 'Interview')
    Interview.objects.filter(status='assigned').update(status='invited')
    Interview.objects.filter(status='declined').update(status='cancelled')
    History = apps.get_model('interviews', 'InterviewStatusHistory')
    History.objects.filter(from_status='assigned').update(from_status='invited')
    History.objects.filter(to_status='assigned').update(to_status='invited')
    History.objects.filter(from_status='declined').update(from_status='cancelled')
    History.objects.filter(to_status='declined').update(to_status='cancelled')


choices = [('invited', 'Invited'), ('scheduled', 'Scheduled'), ('cancelled', 'Cancelled'), ('completed', 'Completed'), ('evaluation_submitted', 'Evaluation Submitted')]


class Migration(migrations.Migration):
    dependencies = [('interviews', '0010_panel_interviewers')]
    operations = [
        migrations.RunPython(map_interview_statuses, migrations.RunPython.noop),
        migrations.RemoveConstraint(model_name='interview', name='unique_active_interview_booking_time'),
        migrations.AlterField(model_name='interview', name='status', field=models.CharField(choices=choices, default='invited', max_length=30)),
        migrations.AlterField(model_name='interviewstatushistory', name='from_status', field=models.CharField(choices=choices, max_length=30)),
        migrations.AlterField(model_name='interviewstatushistory', name='to_status', field=models.CharField(choices=choices, max_length=30)),
        migrations.AddConstraint(
            model_name='interview',
            constraint=models.UniqueConstraint(
                fields=('interviewer', 'interview_date', 'start_time', 'end_time'),
                condition=Q(status__in=['invited', 'scheduled']),
                name='unique_active_interview_booking_time',
            ),
        ),
    ]
