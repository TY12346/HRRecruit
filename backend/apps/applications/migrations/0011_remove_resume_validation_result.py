from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('applications', '0010_simplify_job_application_statuses')]
    operations = [
        migrations.RemoveField(
            model_name='jobapplication',
            name='resume_validation_result',
        ),
    ]
