from django.db import migrations, models


def map_job_statuses(apps, schema_editor):
    JobPosting = apps.get_model('jobs', 'JobPosting')
    JobPosting.objects.filter(status='draft').update(status='drafting')
    JobPosting.objects.exclude(status__in=('drafting', 'open')).update(status='closed')


class Migration(migrations.Migration):
    dependencies = [('jobs', '0014_jobposting_requirements_locked_at')]
    operations = [
        migrations.RunPython(map_job_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='jobposting',
            name='status',
            field=models.CharField(
                choices=[('drafting', 'Drafting'), ('open', 'Open'), ('closed', 'Closed')],
                default='drafting',
                max_length=40,
            ),
        ),
    ]
