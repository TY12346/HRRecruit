from decimal import Decimal

from django.db import migrations, models


def populate_importance_levels(apps, schema_editor):
    JobRequirement = apps.get_model('jobs', 'JobRequirement')
    EvaluationCriterion = apps.get_model('jobs', 'EvaluationCriterion')

    requirement_levels = (
        ('must_have', Decimal('0.40')),
        ('important', Decimal('0.30')),
        ('nice_to_have', Decimal('0.20')),
        ('optional', Decimal('0.10')),
    )
    criterion_levels = (
        ('core', Decimal('0.40')),
        ('standard', Decimal('0.30')),
        ('supporting', Decimal('0.20')),
        ('minor', Decimal('0.10')),
    )

    for requirement in JobRequirement.objects.all().iterator():
        requirement.importance_level = min(
            requirement_levels,
            key=lambda level: abs(level[1] - requirement.weight_score),
        )[0]
        requirement.save(update_fields=['importance_level'])

    for criterion in EvaluationCriterion.objects.all().iterator():
        criterion.importance_level = min(
            criterion_levels,
            key=lambda level: abs(level[1] - criterion.weight_score),
        )[0]
        criterion.save(update_fields=['importance_level'])


class Migration(migrations.Migration):
    dependencies = [('jobs', '0018_use_typed_ulids')]

    operations = [
        migrations.AddField(
            model_name='jobrequirement',
            name='importance_level',
            field=models.CharField(
                choices=[
                    ('must_have', 'Must-have'),
                    ('important', 'Important'),
                    ('nice_to_have', 'Nice-to-have'),
                    ('optional', 'Optional'),
                ],
                default='important',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='evaluationcriterion',
            name='importance_level',
            field=models.CharField(
                choices=[
                    ('core', 'Core competency'),
                    ('standard', 'Standard competency'),
                    ('supporting', 'Supporting competency'),
                    ('minor', 'Minor competency'),
                ],
                default='standard',
                max_length=20,
            ),
        ),
        migrations.RunPython(populate_importance_levels, migrations.RunPython.noop),
    ]
