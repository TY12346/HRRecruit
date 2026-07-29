import uuid

from django.db import migrations, models


MODEL_PREFIXES = {
    'JobApplication': 'APP',
    'ApplicationStageHistory': 'ASH',
    'EmployerInvite': 'INV'
}


def populate_public_ids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('applications', model_name)
        for record in model.objects.filter(public_id__isnull=True).iterator():
            record.public_id = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
            record.save(update_fields=['public_id'])


class Migration(migrations.Migration):
    dependencies = [('applications', '0013_rename_shortlisted_status_to_under_review')]

    operations = [
        migrations.AddField(model_name='jobapplication', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='applicationstagehistory', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='employerinvite', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(model_name='jobapplication', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='applicationstagehistory', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='employerinvite', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
    ]
