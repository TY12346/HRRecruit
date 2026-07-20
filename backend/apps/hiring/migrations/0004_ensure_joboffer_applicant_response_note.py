from django.db import migrations


class Migration(migrations.Migration):
    """Repair databases where the already-applied 0002 migration lacks this column."""

    dependencies = [
        ('hiring', '0003_jobhiringdecision_jobhiringdecisionitem'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE hiring_joboffer '
                "ADD COLUMN IF NOT EXISTS applicant_response_note text NOT NULL DEFAULT '';"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
