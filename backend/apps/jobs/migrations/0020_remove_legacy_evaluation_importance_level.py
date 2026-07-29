from django.db import migrations


def remove_legacy_importance_level(apps, schema_editor):
    """Remove the obsolete scorecard column left outside migration state."""
    evaluation_criterion = apps.get_model('jobs', 'EvaluationCriterion')
    table_name = evaluation_criterion._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }

    if 'importance_level' in columns:
        schema_editor.execute(
            f'ALTER TABLE {schema_editor.quote_name(table_name)} '
            f'DROP COLUMN {schema_editor.quote_name("importance_level")}'
        )


class Migration(migrations.Migration):
    dependencies = [
        ('jobs', '0019_remove_legacy_importance_level'),
    ]

    operations = [
        migrations.RunPython(remove_legacy_importance_level, migrations.RunPython.noop),
    ]
