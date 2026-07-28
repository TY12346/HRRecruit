from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('jobs', '0015_simplify_job_posting_statuses')]

    operations = [
        migrations.AlterField(
            model_name='jobrequisition',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                    ('cancelled', 'Cancelled'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
