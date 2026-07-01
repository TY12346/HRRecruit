from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0008_google_calendar_credentials'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarevent',
            name='provider',
            field=models.CharField(default='google_calendar', max_length=100),
        ),
    ]
