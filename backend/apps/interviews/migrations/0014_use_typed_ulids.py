import secrets
import time

from django.db import migrations, models


ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
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


def encode(value, length):
    result = []
    for _ in range(length):
        value, remainder = divmod(value, 32)
        result.append(ALPHABET[remainder])
    return ''.join(reversed(result))


def replace_public_ids_with_typed_ulids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('interviews', model_name)
        for record in model.objects.all().iterator():
            timestamp = encode(int(time.time_ns() // 1_000_000), 10)
            randomness = encode(secrets.randbits(80), 16)
            record.public_id = f'{prefix}-{timestamp}{randomness}'
            record.save(update_fields=['public_id'])


class Migration(migrations.Migration):
    dependencies = [('interviews', '0013_add_public_ids')]

    operations = [
        migrations.AlterField(model_name='intervieweravailabilitypattern', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='interviewerunavailabledate', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='intervieweravailabilityslot', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='interviewschedulingrequest', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='interview', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='interviewstatushistory', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='googlecalendarcredential', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='calendarevent', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.RunPython(replace_public_ids_with_typed_ulids, migrations.RunPython.noop),
    ]
