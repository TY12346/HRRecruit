import uuid

from django.db import migrations, models


MODEL_PREFIXES = {
    'InterviewRecording': 'REC',
    'InterviewTranscript': 'TRN',
    'InterviewAISummary': 'AIS',
    'InterviewEvaluation': 'EVL',
    'EvaluationAnswer': 'EVA'
}


def populate_public_ids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('evaluations', model_name)
        for record in model.objects.filter(public_id__isnull=True).iterator():
            record.public_id = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
            record.save(update_fields=['public_id'])


class Migration(migrations.Migration):
    dependencies = [('evaluations', '0005_interviewtranscript_low_quality_status')]

    operations = [
        migrations.AddField(model_name='interviewrecording', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='interviewtranscript', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='interviewaisummary', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='interviewevaluation', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='evaluationanswer', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(model_name='interviewrecording', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='interviewtranscript', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='interviewaisummary', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='interviewevaluation', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='evaluationanswer', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
    ]
