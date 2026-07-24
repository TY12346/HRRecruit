from django.db import migrations, models
from django.utils import timezone


def lock_requirements_for_posted_jobs(apps, schema_editor):
    JobPosting = apps.get_model('jobs', 'JobPosting')
    JobPosting.objects.exclude(status='draft').update(requirements_locked_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0013_jobposting_application_deadline_jobposting_vacancies_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobposting',
            name='requirements_locked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(lock_requirements_for_posted_jobs, migrations.RunPython.noop),
    ]
