from django.apps import apps
from django.test import SimpleTestCase

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

    def test_generated_id_contains_prefix_and_random_readable_suffix(self):
        public_id = generate_readable_id('APP')

        self.assertRegex(public_id, r'^APP-[0-9A-F]{12}$')
