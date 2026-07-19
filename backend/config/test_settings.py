from django.core.mail import get_connection
from django.test import SimpleTestCase, override_settings


class EmailSettingsTests(SimpleTestCase):
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST='smtp.example.com',
        EMAIL_PORT=587,
        EMAIL_HOST_USER='sender@example.com',
        EMAIL_HOST_PASSWORD='app-password',
        EMAIL_USE_TLS=True,
        EMAIL_USE_SSL=False,
        EMAIL_TIMEOUT=10,
        DEFAULT_FROM_EMAIL='sender@example.com',
    )
    def test_smtp_backend_receives_configured_connection_settings(self):
        connection = get_connection()

        self.assertEqual(connection.host, 'smtp.example.com')
        self.assertEqual(connection.port, 587)
        self.assertEqual(connection.username, 'sender@example.com')
        self.assertEqual(connection.password, 'app-password')
        self.assertTrue(connection.use_tls)
        self.assertFalse(connection.use_ssl)
        self.assertEqual(connection.timeout, 10)
