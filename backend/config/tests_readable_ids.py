from unittest.mock import patch

from django.apps import apps
from django.test import SimpleTestCase

from apps.billing.models import SubscriptionPlan
from apps.billing.serializers import SubscriptionPlanSerializer
from apps.common.models import READABLE_ID_PREFIXES, ReadableIdModel, generate_readable_id


class ReadableIdModelTests(SimpleTestCase):
    def test_every_domain_model_has_a_registered_readable_id(self):
        domain_app_labels = {label.split('.')[0] for label in READABLE_ID_PREFIXES}
        domain_models = [
            model for model in apps.get_models() if model._meta.app_label in domain_app_labels
        ]
        # The explicit label set is the source of truth; this assertion also makes
        # adding a model without selecting a meaningful prefix fail loudly.
        expected_labels = set(READABLE_ID_PREFIXES)
        actual_labels = {
            model._meta.label
            for model in apps.get_models()
            if model._meta.app_label in domain_app_labels
        }
        self.assertEqual(actual_labels, expected_labels)
        for model in domain_models:
            self.assertTrue(issubclass(model, ReadableIdModel))
            self.assertTrue(model._meta.get_field('public_id').unique)
            self.assertEqual(model._meta.get_field('public_id').max_length, 30)

    def test_generated_id_contains_prefix_and_random_readable_suffix(self):
        public_id = generate_readable_id('APP')

        self.assertRegex(public_id, r'^APP-[0-9A-HJKMNP-TV-Z]{26}$')

    @patch('apps.common.models.secrets.randbits', return_value=0)
    @patch('apps.common.models.time.time_ns')
    def test_generated_ids_sort_by_creation_time(self, time_ns, _randbits):
        time_ns.side_effect = [1_000_000_000, 2_000_000_000]

        first = generate_readable_id('JOB')
        second = generate_readable_id('JOB')

        self.assertLess(first, second)

    def test_api_id_is_the_typed_id_not_the_database_primary_key(self):
        plan = SubscriptionPlan(
            id=42,
            public_id='PLN-01J00000000000000000000000',
            name=SubscriptionPlan.Name.STARTER,
            max_hiring_managers=1,
            max_recruiters=1,
            max_interviewers=1,
            max_active_job_postings=1,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            price='0.00',
            features_description='',
        )

        payload = SubscriptionPlanSerializer(plan).data

        self.assertEqual(payload['id'], plan.public_id)
        self.assertNotIn('public_id', payload)
