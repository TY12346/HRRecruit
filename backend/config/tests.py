from django.test import SimpleTestCase
from rest_framework import status

from .exceptions import clean_exception_handler


class CleanExceptionHandlerTests(SimpleTestCase):
    def test_logs_unhandled_exceptions_without_exposing_them_to_the_client(self):
        class JobOfferView:
            pass

        try:
            raise RuntimeError('Database column is missing')
        except RuntimeError as exc:
            with self.assertLogs('config.exceptions', level='ERROR') as logs:
                response = clean_exception_handler(exc, {'view': JobOfferView()})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {'detail': 'Internal server error.'})
        self.assertIn('Unhandled API exception in JobOfferView.', logs.output[0])
        self.assertIn('RuntimeError: Database column is missing', logs.output[0])
