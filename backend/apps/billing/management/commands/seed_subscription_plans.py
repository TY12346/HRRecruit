from django.core.management.base import BaseCommand

from apps.billing.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Seed default subscription plans for the demo billing flow.'

    def handle(self, *args, **options):
        plans = [
            {
                'name': SubscriptionPlan.Name.BASIC,
                'billing_cycle': SubscriptionPlan.BillingCycle.MONTHLY,
                'max_job_postings': 3,
                'price': '0.00',
                'features_description': 'Basic demo plan for small teams with limited open job postings.',
                'is_active': True,
            },
            {
                'name': SubscriptionPlan.Name.PRO,
                'billing_cycle': SubscriptionPlan.BillingCycle.MONTHLY,
                'max_job_postings': 20,
                'price': '99.00',
                'features_description': 'Pro demo plan for growing teams with more open job postings.',
                'is_active': True,
            },
            {
                'name': SubscriptionPlan.Name.ENTERPRISE,
                'billing_cycle': SubscriptionPlan.BillingCycle.YEARLY,
                'max_job_postings': 100,
                'price': '999.00',
                'features_description': 'Enterprise demo plan for large organizations with expanded hiring needs.',
                'is_active': True,
            },
        ]

        for plan in plans:
            subscription_plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan['name'],
                billing_cycle=plan['billing_cycle'],
                defaults={
                    'max_job_postings': plan['max_job_postings'],
                    'price': plan['price'],
                    'features_description': plan['features_description'],
                    'is_active': plan['is_active'],
                },
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} {subscription_plan}'))
