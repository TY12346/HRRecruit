from django.core.management.base import BaseCommand
from apps.billing.models import SubscriptionPlan

FEATURES = 'All HRRecruit features are included. This plan differs only by organization capacity.'
PLANS = [
    (SubscriptionPlan.Name.STARTER, SubscriptionPlan.BillingCycle.MONTHLY, 1, 1, 3, 2, '29.00'),
    (SubscriptionPlan.Name.BASIC, SubscriptionPlan.BillingCycle.MONTHLY, 2, 3, 10, 10, '0.00'),
    (SubscriptionPlan.Name.PROFESSIONAL, SubscriptionPlan.BillingCycle.MONTHLY, 5, 10, 50, 30, '99.00'),
    (SubscriptionPlan.Name.ENTERPRISE, SubscriptionPlan.BillingCycle.YEARLY, 10, 25, 100, 100, '999.00'),
]

class Command(BaseCommand):
    help = 'Idempotently seed the four capacity-only demo subscription plans.'

    def handle(self, *args, **options):
        seeded_keys = {(name, cycle) for name, cycle, *_ in PLANS}
        for name, cycle, managers, recruiters, interviewers, jobs, price in PLANS:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=name, billing_cycle=cycle,
                defaults={'max_hiring_managers': managers, 'max_recruiters': recruiters,
                          'max_interviewers': interviewers, 'max_active_job_postings': jobs,
                          'price': price, 'features_description': FEATURES, 'is_active': True},
            )
            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"} {plan}'))
        for plan in SubscriptionPlan.objects.filter(is_active=True):
            if (plan.name, plan.billing_cycle) not in seeded_keys:
                plan.is_active = False
                plan.save(update_fields=['is_active'])
