from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('users', '0007_hiring_manager_role_labels')]
    operations = [
        migrations.RemoveField(
            model_name='applicantresume',
            name='validation_result',
        ),
    ]
