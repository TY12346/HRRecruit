
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarevent',
            name='calendar_link',
            field=models.URLField(blank=True, max_length=1000),
        ),
    ]
