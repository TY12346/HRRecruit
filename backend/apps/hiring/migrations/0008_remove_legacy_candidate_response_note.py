from django.db import migrations


REPAIR_LEGACY_RESPONSE_NOTE_SQL = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'hiring_joboffer'
          AND column_name = 'candidate_response_note'
    ) THEN
        UPDATE hiring_joboffer
        SET applicant_response_note = candidate_response_note
        WHERE candidate_response_note IS NOT NULL
          AND candidate_response_note <> ''
          AND (applicant_response_note IS NULL OR applicant_response_note = '');

        ALTER TABLE hiring_joboffer DROP COLUMN candidate_response_note;
    END IF;
END $$;
"""


class Migration(migrations.Migration):
    """Remove a legacy unmanaged column that can block new offer inserts."""

    dependencies = [('hiring', '0007_job_offer_approval_workflow')]

    operations = [
        migrations.RunSQL(
            sql=REPAIR_LEGACY_RESPONSE_NOTE_SQL,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
