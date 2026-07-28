from django.db import migrations, models

FEATURES = 'All HRRecruit features are included. This plan differs only by organization capacity.'
MATRIX = {
    'Starter': (1, 1, 3, 2, '29.00', 'monthly'),
    'Basic': (2, 3, 10, 10, '0.00', 'monthly'),
    'Professional': (5, 10, 50, 30, '99.00', 'monthly'),
    'Enterprise': (10, 25, 100, 100, '999.00', 'yearly'),
}

def forwards(apps, schema_editor):
    Plan = apps.get_model('billing', 'SubscriptionPlan')
    # Rename the existing row in place so its subscriptions, payments and invoices retain their FK chain.
    for plan in Plan.objects.filter(name='Pro'):
        target = Plan.objects.filter(name='Professional', billing_cycle=plan.billing_cycle).first()
        if target:
            apps.get_model('billing', 'Subscription').objects.filter(plan=plan).update(plan=target)
            plan.delete()  # now unreferenced; preserves every subscription/payment/invoice relationship
        else:
            plan.name = 'Professional'
            plan.save(update_fields=['name'])
    for name, (hm, rec, interviewer, jobs, price, cycle) in MATRIX.items():
        plan, _ = Plan.objects.get_or_create(name=name, billing_cycle=cycle, defaults={'price': price})
        plan.max_hiring_managers = hm
        plan.max_recruiters = rec
        plan.max_interviewers = interviewer
        plan.max_active_job_postings = jobs
        plan.features_description = FEATURES
        plan.is_active = True
        plan.save()
    valid_keys = {(name, values[-1]) for name, values in MATRIX.items()}
    for plan in Plan.objects.filter(is_active=True):
        if (plan.name, plan.billing_cycle) not in valid_keys:
            plan.is_active = False
            plan.save(update_fields=['is_active'])

def backwards(apps, schema_editor):
    Plan = apps.get_model('billing', 'SubscriptionPlan')
    Plan.objects.filter(name='Professional').update(name='Pro')

class Migration(migrations.Migration):
    dependencies = [('billing', '0004_subscription_cancellation_payment_metadata')]
    operations = [
        migrations.RenameField(model_name='subscriptionplan', old_name='max_job_postings', new_name='max_active_job_postings'),
        migrations.AddField(model_name='subscriptionplan', name='max_hiring_managers', field=models.PositiveIntegerField(default=1), preserve_default=False),
        migrations.AddField(model_name='subscriptionplan', name='max_recruiters', field=models.PositiveIntegerField(default=1), preserve_default=False),
        migrations.AddField(model_name='subscriptionplan', name='max_interviewers', field=models.PositiveIntegerField(default=3), preserve_default=False),
        migrations.AlterField(model_name='subscriptionplan', name='name', field=models.CharField(choices=[('Starter', 'Starter'), ('Basic', 'Basic'), ('Professional', 'Professional'), ('Enterprise', 'Enterprise')], max_length=50)),
        migrations.RunPython(forwards, backwards),
    ]
