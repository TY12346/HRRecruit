import uuid

from django.db import migrations, models


MODEL_PREFIXES = {
    'Organization': 'ORG',
    'OrganizationMembership': 'MEM'
}


def populate_public_ids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('organizations', model_name)
        for record in model.objects.filter(public_id__isnull=True).iterator():
            record.public_id = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
            record.save(update_fields=['public_id'])


class Migration(migrations.Migration):
    dependencies = [('organizations', '0002_hiring_manager_role_labels')]

    operations = [
        migrations.AddField(model_name='organization', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='organizationmembership', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(model_name='organization', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='organizationmembership', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
    ]
