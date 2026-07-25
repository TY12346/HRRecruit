from django.db import migrations, models
from django.db.models import Q


def map_application_statuses(apps, schema_editor):
    JobApplication = apps.get_model('applications', 'JobApplication')
    rejected = ('withdrawn', 'screened_not_qualified', 'rejected', 'interview_declined', 'hr_rejected', 'offer_declined')
    JobApplication.objects.filter(status__in=rejected).update(status='rejected')
    JobApplication.objects.filter(status__in=('submitted', 'screened', 'screened_qualified')).update(status='applied')
    JobApplication.objects.exclude(status__in=('applied', 'rejected')).update(status='shortlisted')

    StageHistory = apps.get_model('applications', 'ApplicationStageHistory')
    StageHistory.objects.filter(from_stage__in=rejected).update(from_stage='rejected')
    StageHistory.objects.filter(to_stage__in=rejected).update(to_stage='rejected')
    StageHistory.objects.filter(from_stage__in=('submitted', 'screened', 'screened_qualified')).update(from_stage='applied')
    StageHistory.objects.filter(to_stage__in=('submitted', 'screened', 'screened_qualified')).update(to_stage='applied')
    StageHistory.objects.exclude(from_stage__in=('applied', 'rejected')).update(from_stage='shortlisted')
    StageHistory.objects.exclude(to_stage__in=('applied', 'rejected')).update(to_stage='shortlisted')


choices = [('applied', 'Applied'), ('shortlisted', 'Shortlisted'), ('rejected', 'Rejected')]


class Migration(migrations.Migration):
    dependencies = [('applications', '0009_employerinvite')]
    operations = [
        migrations.RunPython(map_application_statuses, migrations.RunPython.noop),
        migrations.RemoveConstraint(model_name='jobapplication', name='unique_job_application'),
        migrations.AlterField(model_name='jobapplication', name='status', field=models.CharField(choices=choices, default='applied', max_length=30)),
        migrations.AlterField(model_name='applicationstagehistory', name='from_stage', field=models.CharField(choices=choices, max_length=30)),
        migrations.AlterField(model_name='applicationstagehistory', name='to_stage', field=models.CharField(choices=choices, max_length=30)),
        migrations.AddConstraint(
            model_name='jobapplication',
            constraint=models.UniqueConstraint(fields=('applicant', 'job'), condition=~Q(status='rejected'), name='unique_job_application'),
        ),
    ]
