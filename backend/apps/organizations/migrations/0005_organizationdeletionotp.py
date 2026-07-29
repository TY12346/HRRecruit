import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0004_use_typed_ulids'),
        ('users', '0010_use_typed_ulids'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationDeletionOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.CharField(editable=False, max_length=30, unique=True)),
                ('code_hash', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deletion_otps', to='organizations.organization')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_deletion_otps', to='users.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
