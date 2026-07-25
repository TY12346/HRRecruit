from django.db import migrations, models


def map_offer_statuses(apps, schema_editor):
    JobOffer = apps.get_model('hiring', 'JobOffer')
    JobOffer.objects.filter(offer_status='sent').update(offer_status='offer_sent')
    JobOffer.objects.filter(offer_status='accepted').update(offer_status='offer_accepted')
    JobOffer.objects.filter(offer_status__in=('declined', 'expired', 'withdrawn')).update(offer_status='offer_declined')


class Migration(migrations.Migration):
    dependencies = [('hiring', '0005_rename_job_hiring_models_to_decisions')]
    operations = [
        migrations.RunPython(map_offer_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='joboffer',
            name='offer_status',
            field=models.CharField(
                choices=[('drafting', 'Drafting'), ('offer_pending_approval', 'Offer Pending Approval'), ('offer_sent', 'Offer Sent'), ('offer_accepted', 'Offer Accepted'), ('offer_declined', 'Offer Declined')],
                default='offer_sent',
                max_length=30,
            ),
        ),
    ]
