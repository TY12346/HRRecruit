from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0003_passwordresetotp'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicantEducation',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('school_name', models.CharField(max_length=255)),
                ('degree_name', models.CharField(blank=True, max_length=255)),
                ('field_of_study', models.CharField(blank=True, max_length=255)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('grade', models.CharField(blank=True, max_length=100)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='educations', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-start_date', '-id']},
        ),
        migrations.CreateModel(
            name='ApplicantExperience',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('job_title', models.CharField(max_length=255)),
                ('employment_type', models.CharField(blank=True, max_length=100)),
                ('company_name', models.CharField(blank=True, max_length=255)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiences', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-start_date', '-id']},
        ),
        migrations.CreateModel(
            name='ApplicantSkill',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('skill_name', models.CharField(max_length=100)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['skill_name'], 'unique_together': {('applicant', 'skill_name')}},
        ),
    ]
