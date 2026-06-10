# HRRecruit Deployment Notes

This document records deployment assumptions and production considerations for the HRRecruit FYP prototype.

## Local/Demo Deployment Assumptions

The current repository is suitable for local FYP demonstration with:

- PostgreSQL running locally.
- Django REST Framework backend running with `python manage.py runserver`.
- React web portal running with Vite.
- Flutter app running on an emulator or development device.
- Local media storage for uploaded resumes and interview recordings.
- Console email backend.
- Demo/fallback AI, transcription, summary, and payment behavior.

This setup is not a full production deployment pipeline.

## Backend Environment Variables

Create `backend/.env` for local/demo use. Common settings:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key. Use a strong value outside local demo. |
| `DJANGO_DEBUG` | Use `True` for local development; use `False` outside development. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts, including LAN IP for physical mobile testing. |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Comma-separated web/mobile development origins. |
| `POSTGRES_DB` | PostgreSQL database name. |
| `POSTGRES_USER` | PostgreSQL username. |
| `POSTGRES_PASSWORD` | PostgreSQL password. |
| `POSTGRES_HOST` | PostgreSQL host. |
| `POSTGRES_PORT` | PostgreSQL port, usually `5432`. |
| `DEFAULT_FROM_EMAIL` | Sender email used by local/demo email code. |
| `SENDGRID_API_KEY` | Optional SendGrid key; leave blank unless real email integration is configured. |
| `OPENAI_API_KEY` | Optional AI/ASR/LLM key; leave blank for fallback behavior. |
| `STRIPE_SECRET_KEY` | Optional Stripe key; leave blank for demo payment behavior. |
| `STRIPE_WEBHOOK_SECRET` | Optional Stripe webhook secret. |
| `STRIPE_CHECKOUT_SUCCESS_URL` | Optional checkout success URL. |
| `STRIPE_CHECKOUT_CANCEL_URL` | Optional checkout cancel URL. |
| `STRIPE_CURRENCY` | Payment currency, default `MYR`. |

## Frontend API Base URL Configuration

The React web portal reads the backend base URL from `web/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

For deployed environments, set this to the deployed Django API base URL.

## Mobile API Base URL Configuration

The Flutter app defaults to Android emulator local backend access:

```text
http://10.0.2.2:8000/api/
```

For physical-device testing, use the backend computer's LAN IP:

```text
http://YOUR_COMPUTER_LAN_IP:8000/api/
```

The app can also be launched with:

```bash
flutter run --dart-define=HRRECRUIT_API_BASE_URL=http://YOUR_COMPUTER_LAN_IP:8000/api/
```

For production, configure HTTPS and a stable API domain.

## PostgreSQL Requirement

The backend is configured for PostgreSQL and should not be switched to SQLite for the FYP demo. Ensure:

- Database exists before migration.
- Credentials are set in `backend/.env`.
- Database backups are configured for any non-demo deployment.
- Separate development/demo/production databases are used.

## Static and Media Files

Current local/demo behavior uses Django local media storage:

- Resume uploads.
- Interview recording uploads.
- Generated or stored local media artifacts.

For production, plan proper static/media handling:

- Run `python manage.py collectstatic` if serving Django static files in production.
- Use a production web server or platform static hosting.
- Use secure media storage with access controls.
- Validate file size/type and keep upload permissions enforced.
- Do not expose private resumes or recordings publicly.

## Optional Integrations

Optional integrations should remain disabled unless valid credentials and a suitable deployment environment are configured.

### SendGrid/email

The local/demo project uses Django console email behavior. Real SendGrid email requires:

- Valid `SENDGRID_API_KEY`.
- Verified sender/domain.
- Email backend changes if production SendGrid delivery is required.
- Testing for OTP/password-reset delivery.

### Google Calendar

Calendar integration is not enabled by default in the current demo setup. Treat it as optional/future unless code, OAuth credentials, callback URLs, scopes, and tests are explicitly added.

### Stripe/PayPal/FPX/payment

The repository includes billing and demo payment behavior, plus optional Stripe-related settings/endpoints. For FYP demonstration, use demo payment records/flow. Real payment gateway setup requires:

- Valid gateway credentials.
- Webhook configuration and public callback URL.
- Sandbox testing.
- Production compliance and security review.

Do not claim PayPal/FPX/real Stripe payments are production-ready unless implemented, configured, and tested.

### OpenAI/Whisper/LLM/ASR

AI resume screening is implemented through the local AI service layer and may use fallback behavior. Transcription and summaries can use mock/demo fallbacks. Real AI/ASR/LLM setup would require:

- Valid credentials such as `OPENAI_API_KEY` if supported by the relevant service file.
- Cost/rate-limit/error handling.
- Privacy review for resumes and interview recordings.
- Tests that mock external API calls.

## Security and Production Hardening Notes

For any deployment beyond the FYP demo:

- Set `DJANGO_DEBUG=False`.
- Use strong `DJANGO_SECRET_KEY`.
- Use HTTPS for web and mobile API traffic.
- Restrict `DJANGO_ALLOWED_HOSTS` and CORS origins.
- Configure secure cookies and proxy headers if using a reverse proxy.
- Add request throttling/rate limiting for authentication and OTP/password-reset endpoints.
- Review file-upload scanning and storage policies.
- Avoid logging sensitive personal data, resumes, recordings, tokens, or payment details.

## Recommended FYP Demo Deployment

For examiner/demo review, the recommended setup is local/demo mode:

1. PostgreSQL local database.
2. Django backend on `localhost:8000` or LAN IP for mobile.
3. React web portal on `localhost:5173`.
4. Flutter app on emulator or local device.
5. Seeded demo data.
6. Optional integrations left blank/disabled.

This demonstrates the complete FYP workflow without relying on external paid services.
