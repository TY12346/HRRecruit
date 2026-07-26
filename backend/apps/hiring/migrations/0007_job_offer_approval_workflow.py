from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_offer_statuses(apps, schema_editor):
    JobOffer = apps.get_model('hiring', 'JobOffer')
    mapping = {
        'offer_pending_approval': 'pending_hr_approval',
        'offer_sent': 'pending_applicant_response',
        'offer_accepted': 'accepted_by_applicant',
        'offer_declined': 'rejected_by_applicant',
    }
    for old, new in mapping.items():
        JobOffer.objects.filter(offer_status=old).update(offer_status=new)


class Migration(migrations.Migration):
    dependencies = [('hiring', '0006_expand_job_offer_statuses'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='joboffer', name='hiring_manager_remarks', field=models.TextField(blank=True)),
        migrations.AddField(model_name='joboffer', name='reviewed_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='joboffer', name='reviewed_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_job_offers', to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name='joboffer', name='offer_status', field=models.CharField(choices=[('drafting', 'Drafting'), ('pending_hr_approval', 'Pending Approval by Hiring Manager'), ('approved_by_hr', 'Approved by Hiring Manager'), ('pending_applicant_response', 'Pending Applicant Response'), ('disapproved_by_hr', 'Disapproved by Hiring Manager'), ('accepted_by_applicant', 'Accepted by Applicant'), ('rejected_by_applicant', 'Rejected by Applicant')], default='drafting', max_length=30)),
        migrations.RunPython(migrate_offer_statuses, migrations.RunPython.noop),
    ]
