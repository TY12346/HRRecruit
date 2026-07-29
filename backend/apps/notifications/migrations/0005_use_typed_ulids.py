import secrets
import time

from django.db import migrations, models


ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
MODEL_PREFIXES = {
    'Notification': 'NTF',
    'PushDevice': 'DEV'
}


def encode(value, length):
    result = []
    for _ in range(length):
        value, remainder = divmod(value, 32)
        result.append(ALPHABET[remainder])
    return ''.join(reversed(result))


def replace_public_ids_with_typed_ulids(apps, schema_editor):
    for model_name, prefix in MODEL_PREFIXES.items():
        model = apps.get_model('notifications', model_name)
        for record in model.objects.all().iterator():
            timestamp = encode(int(time.time_ns() // 1_000_000), 10)
            randomness = encode(secrets.randbits(80), 16)
            record.public_id = f'{prefix}-{timestamp}{randomness}'
            record.save(update_fields=['public_id'])


def replace_related_integer_ids(apps, schema_editor):
    notification_model = apps.get_model('notifications', 'Notification')
    models_by_name = {model._meta.model_name: model for model in apps.get_models()}
    for notification in notification_model.objects.exclude(related_entity_id__isnull=True).exclude(related_entity_id='').iterator():
        related_model = models_by_name.get(notification.related_entity_type.lower())
        if related_model is None:
            continue
        related = related_model.objects.filter(pk=notification.related_entity_id).first()
        if related is not None and hasattr(related, 'public_id'):
            notification.related_entity_id = related.public_id
            notification.save(update_fields=['related_entity_id'])


class Migration(migrations.Migration):
    dependencies = [
        ('applications', '0015_use_typed_ulids'),
        ('billing', '0007_use_typed_ulids'),
        ('evaluations', '0007_use_typed_ulids'),
        ('hiring', '0010_use_typed_ulids'),
        ('interviews', '0014_use_typed_ulids'),
        ('jobs', '0018_use_typed_ulids'),
        ('notifications', '0004_add_public_ids'),
        ('organizations', '0004_use_typed_ulids'),
        ('users', '0010_use_typed_ulids'),
    ]

    operations = [
        migrations.AlterField(model_name='notification', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.AlterField(model_name='pushdevice', name='public_id', field=models.CharField(editable=False, max_length=30, unique=True)),
        migrations.RunPython(replace_public_ids_with_typed_ulids, migrations.RunPython.noop),
        migrations.AlterField(model_name='notification', name='related_entity_id', field=models.CharField(blank=True, max_length=30, null=True)),
        migrations.RunPython(replace_related_integer_ids, migrations.RunPython.noop),
    ]
