import uuid

from django.db import migrations, models


MODEL_PREFIXES = {
    'InterviewerAvailabilityPattern': 'AVP',
    'InterviewerUnavailableDate': 'UVD',
    'InterviewerAvailabilitySlot': 'AVS',
    'InterviewSchedulingRequest': 'ISR',
    'Interview': 'INT',
    'InterviewStatusHistory': 'ISH',
    'GoogleCalendarCredential': 'GCC',
    'CalendarEvent': 'CAL'
}


def populate_public_ids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('interviews', model_name)
        for record in model.objects.filter(public_id__isnull=True).iterator():
            record.public_id = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
            record.save(update_fields=['public_id'])


class Migration(migrations.Migration):
    dependencies = [('interviews', '0012_interviewschedulingrequest_invitation_sent_at')]

    operations = [
        migrations.AddField(model_name='intervieweravailabilitypattern', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='interviewerunavailabledate', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='intervieweravailabilityslot', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='interviewschedulingrequest', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='interview', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='interviewstatushistory', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='googlecalendarcredential', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='calendarevent', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(model_name='intervieweravailabilitypattern', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='interviewerunavailabledate', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='intervieweravailabilityslot', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='interviewschedulingrequest', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='interview', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='interviewstatushistory', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='googlecalendarcredential', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='calendarevent', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
    ]
