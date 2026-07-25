from django.db import migrations, models


def rename_shortlisted_status(apps, schema_editor):
    JobApplication = apps.get_model('applications', 'JobApplication')
    StageHistory = apps.get_model('applications', 'ApplicationStageHistory')

    JobApplication.objects.filter(status='shortlisted').update(status='under_review')
    StageHistory.objects.filter(from_stage='shortlisted').update(from_stage='under_review')
    StageHistory.objects.filter(to_stage='shortlisted').update(to_stage='under_review')


def restore_shortlisted_status(apps, schema_editor):
    JobApplication = apps.get_model('applications', 'JobApplication')
    StageHistory = apps.get_model('applications', 'ApplicationStageHistory')

    JobApplication.objects.filter(status='under_review').update(status='shortlisted')
    StageHistory.objects.filter(from_stage='under_review').update(from_stage='shortlisted')
    StageHistory.objects.filter(to_stage='under_review').update(to_stage='shortlisted')


choices = [('under_review', 'Under review'), ('rejected', 'Rejected')]


class Migration(migrations.Migration):
    dependencies = [('applications', '0012_remove_applied_application_status')]
    operations = [
        migrations.RunPython(rename_shortlisted_status, restore_shortlisted_status),
        migrations.AlterField(
            model_name='jobapplication',
            name='status',
            field=models.CharField(choices=choices, default='under_review', max_length=30),
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
