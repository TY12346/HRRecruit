from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('interviews', '0011_simplify_interview_statuses')]
    operations = [
        migrations.AddField(
            model_name='interviewschedulingrequest',
            name='invitation_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
