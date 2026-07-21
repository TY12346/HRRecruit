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
