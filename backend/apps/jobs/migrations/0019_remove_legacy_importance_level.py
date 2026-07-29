from django.db import migrations


def remove_legacy_importance_level(apps, schema_editor):
    """Remove a column created outside the current Django migration state."""
    job_requirement = apps.get_model('jobs', 'JobRequirement')
    table_name = job_requirement._meta.db_table

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
        ('jobs', '0018_use_typed_ulids'),
    ]

    operations = [
        migrations.RunPython(remove_legacy_importance_level, migrations.RunPython.noop),
    ]
