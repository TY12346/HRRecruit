from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('hiring', '0004_ensure_joboffer_applicant_response_note'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='JobHiringRecommendation',
            new_name='JobHiringDecision',
        ),
        migrations.RenameModel(
            old_name='JobHiringRecommendationItem',
            new_name='JobHiringDecisionItem',
        ),
        migrations.RenameField(
            model_name='jobhiringdecision',
            old_name='recommendation_type',
            new_name='decision_type',
        ),
        migrations.RenameField(
            model_name='jobhiringdecisionitem',
            old_name='recommendation',
            new_name='decision',
        ),
        migrations.AlterField(
            model_name='jobhiringdecision', name='job_posting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hiring_decisions', to='jobs.jobposting'),
        ),
        migrations.AlterField(
            model_name='jobhiringdecision', name='recruiter',
            field=models.ForeignKey(limit_choices_to={'role': 'recruiter'}, on_delete=django.db.models.deletion.PROTECT, related_name='submitted_job_hiring_decisions', to='users.user'),
        ),
        migrations.AlterField(
            model_name='jobhiringdecision', name='reviewed_by',
            field=models.ForeignKey(blank=True, limit_choices_to={'role': 'hr_head'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_job_hiring_decisions', to='users.user'),
        ),
        migrations.AlterField(
            model_name='jobhiringdecisionitem', name='application',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_hiring_decision_items', to='applications.jobapplication'),
        ),
        migrations.RemoveConstraint(model_name='jobhiringdecisionitem', name='unique_job_recommendation_application'),
        migrations.AddConstraint(model_name='jobhiringdecisionitem', constraint=models.UniqueConstraint(fields=('decision', 'application'), name='unique_job_decision_application')),
    ]
