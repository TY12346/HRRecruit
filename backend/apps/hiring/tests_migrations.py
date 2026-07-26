from importlib import import_module

from django.test import SimpleTestCase


class HiringMigrationHistoryTests(SimpleTestCase):
    def test_applied_migration_dependency_is_not_renamed(self):
        """Keep the historical 0003 identifier stable for existing databases."""
        migration = import_module('apps.hiring.migrations.0004_ensure_joboffer_applicant_response_note').Migration

        self.assertEqual(
            migration.dependencies,
            [('hiring', '0003_jobhiringrecommendation_jobhiringrecommendationitem')],
        )

    def test_decision_rename_runs_after_the_existing_migration_chain(self):
        migration = import_module('apps.hiring.migrations.0005_rename_job_hiring_models_to_decisions').Migration

        self.assertEqual(migration.dependencies, [('hiring', '0004_ensure_joboffer_applicant_response_note')])

    def test_legacy_candidate_response_note_repair_preserves_data_before_removal(self):
        migration_module = import_module('apps.hiring.migrations.0008_remove_legacy_candidate_response_note')

        self.assertEqual(migration_module.Migration.dependencies, [('hiring', '0007_job_offer_approval_workflow')])
        self.assertIn('SET applicant_response_note = candidate_response_note', migration_module.REPAIR_LEGACY_RESPONSE_NOTE_SQL)
        self.assertIn('DROP COLUMN candidate_response_note', migration_module.REPAIR_LEGACY_RESPONSE_NOTE_SQL)
