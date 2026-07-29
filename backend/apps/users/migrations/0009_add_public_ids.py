import uuid

from django.db import migrations, models


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


def populate_public_ids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('users', model_name)
        for record in model.objects.filter(public_id__isnull=True).iterator():
            record.public_id = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
            record.save(update_fields=['public_id'])


class Migration(migrations.Migration):
    dependencies = [('users', '0008_remove_applicantresume_validation_result')]

    operations = [
        migrations.AddField(model_name='user', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='applicantprofile', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='applicantresume', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='applicantexperience', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='applicanteducation', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='applicantskill', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='recruiterprofile', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='interviewerprofile', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='hrheadprofile', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.AddField(model_name='passwordresetotp', name='public_id', field=models.CharField(editable=False, max_length=16, null=True, unique=True)),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(model_name='user', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='applicantprofile', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='applicantresume', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='applicantexperience', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='applicanteducation', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='applicantskill', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='recruiterprofile', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='interviewerprofile', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='hrheadprofile', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name='passwordresetotp', name='public_id', field=models.CharField(editable=False, max_length=16, unique=True)),
    ]
