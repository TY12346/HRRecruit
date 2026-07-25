from django.db import migrations, models


def map_applied_statuses(apps, schema_editor):
    JobApplication = apps.get_model('applications', 'JobApplication')
    StageHistory = apps.get_model('applications', 'ApplicationStageHistory')

    for application in JobApplication.objects.filter(status='applied').only('id', 'final_score'):
        mapped_status = (
            'shortlisted'
            if application.final_score is not None and application.final_score >= 60
            else 'rejected'
        )
        JobApplication.objects.filter(id=application.id).update(status=mapped_status)
        StageHistory.objects.filter(application_id=application.id, from_stage='applied').update(
            from_stage=mapped_status
        )
        StageHistory.objects.filter(application_id=application.id, to_stage='applied').update(
            to_stage=mapped_status
        )


choices = [('shortlisted', 'Shortlisted'), ('rejected', 'Rejected')]


class Migration(migrations.Migration):
    dependencies = [('applications', '0011_remove_resume_validation_result')]
    operations = [
        migrations.RunPython(map_applied_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='jobapplication',
            name='status',
            field=models.CharField(choices=choices, default='shortlisted', max_length=30),
        ),
        migrations.AlterField(
            model_name='applicationstagehistory',
            name='from_stage',
            field=models.CharField(choices=choices, max_length=30),
        ),
        migrations.AlterField(
            model_name='applicationstagehistory',
            name='to_stage',
            field=models.CharField(choices=choices, max_length=30),
        ),
    ]
