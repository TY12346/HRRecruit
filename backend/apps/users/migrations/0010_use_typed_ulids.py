import secrets
import time

from django.db import migrations, models


ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
MODEL_PREFIXES = {
    'User': 'USR',
    'ApplicantProfile': 'APF',
    'ApplicantResume': 'RSM',
    'ApplicantExperience': 'EXP',
    'ApplicantEducation': 'EDU',
    'ApplicantSkill': 'SKL',
    'RecruiterProfile': 'RPF',
    'InterviewerProfile': 'IPF',
    'HRHeadProfile': 'HRP',
    'PasswordResetOTP': 'OTP'
}


def encode(value, length):
    result = []
    for _ in range(length):
        value, remainder = divmod(value, 32)
        result.append(ALPHABET[remainder])
    return ''.join(reversed(result))


def replace_public_ids_with_typed_ulids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('users', model_name)
        for record in model.objects.all().iterator():
            timestamp = encode(int(time.time_ns() // 1_000_000), 10)
            randomness = encode(secrets.randbits(80), 16)
            record.public_id = f'{prefix}-{timestamp}{randomness}'
            record.save(update_fields=['public_id'])


class Migration(migrations.Migration):
    dependencies = [('users', '0009_add_public_ids')]

    operations = [
        migrations.AlterField(model_name='user', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='applicantprofile', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='applicantresume', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='applicantexperience', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='applicanteducation', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='applicantskill', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='recruiterprofile', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='interviewerprofile', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='hrheadprofile', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='passwordresetotp', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.RunPython(replace_public_ids_with_typed_ulids, migrations.RunPython.noop),
    ]
