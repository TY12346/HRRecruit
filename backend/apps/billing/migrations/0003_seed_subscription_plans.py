from django.db import migrations


def seed_subscription_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('billing', 'SubscriptionPlan')
    plans = [
        {
            'name': 'Basic',
            'billing_cycle': 'monthly',
            'max_job_postings': 3,
            'price': '0.00',
            'features_description': 'Basic demo plan for small teams with limited open job postings.',
            'is_active': True,
        },
        {
            'name': 'Pro',
            'billing_cycle': 'monthly',
            'max_job_postings': 20,
            'price': '99.00',
            'features_description': 'Pro demo plan for growing teams with more open job postings.',
            'is_active': True,
        },
        {
            'name': 'Enterprise',
            'billing_cycle': 'yearly',
            'max_job_postings': 100,
            'price': '999.00',
            'features_description': 'Enterprise demo plan for large organizations with expanded hiring needs.',
            'is_active': True,
        },
    ]
    for plan in plans:
        SubscriptionPlan.objects.update_or_create(
            name=plan['name'],
            billing_cycle=plan['billing_cycle'],
            defaults={
                'max_job_postings': plan['max_job_postings'],
                'price': plan['price'],
                'features_description': plan['features_description'],
                'is_active': plan['is_active'],
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_alter_payment_invoice_number_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_subscription_plans, migrations.RunPython.noop),
    ]
