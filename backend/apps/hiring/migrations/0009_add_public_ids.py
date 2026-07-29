import uuid

from django.db import migrations, models


MODEL_PREFIXES = {
    'HiringDecision': 'HDC',
    'JobHiringDecision': 'JHD',
    'JobHiringDecisionItem': 'HDI',
    'JobOffer': 'OFR'
}


def populate_public_ids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('hiring', model_name)
        for record in model.objects.filter(public_id__isnull=True).iterator():
            record.public_id = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
            record.save(update_fields=['public_id'])


class Migration(migrations.Migration):
    dependencies = [('hiring', '0008_remove_legacy_candidate_response_note')]

    operations = [
        migrations.AddField(model_name='hiringdecision', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='jobhiringdecision', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='jobhiringdecisionitem', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='joboffer', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(model_name='hiringdecision', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='jobhiringdecision', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='jobhiringdecisionitem', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='joboffer', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
    ]
