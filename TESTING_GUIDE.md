# HRRecruit Testing Guide

This guide explains automated and manual testing for the current HRRecruit FYP implementation.

## Test Environment Requirements

Before running backend tests or checks:

- PostgreSQL must be installed and running.
- `backend/.env` must point to a valid PostgreSQL database.
- Backend dependencies must be installed in the active Python virtual environment.
- External services should be mocked, disabled, or left blank so demo/fallback behavior is used.

## Backend Checks and Tests

From the repository root:

```bash
cd backend
source .venv/bin/activate
```

Run Django configuration checks:

```bash
python manage.py check
```

Run the full backend test suite:

```bash
python manage.py test
```

Run selected tests when focusing on a specific area:

```bash
python manage.py test apps.users.tests_seed_demo_data
python manage.py test apps.applications.tests_business_flow
python manage.py test apps.applications.tests
```

The selected tests above are useful for demo data and important recruitment business-flow coverage.

## React Web Checks

From the repository root:

```bash
cd web
npm install
```

Build the React portal:

```bash
npm run build
```

Run lint if dependencies are installed and the lint command is available:

```bash
npm run lint
```

If `vite` or `eslint` is missing, run `npm install` or `npm ci` before repeating the command.

## Flutter Mobile Checks

From the repository root:

```bash
cd mobile
flutter pub get
flutter analyze
```

If platform tooling is missing, run:

```bash
flutter doctor
```

The mobile app communicates with the backend API, so manual mobile testing also requires the Django server to be running.

## Manual Smoke Test Checklist

Use seeded demo data for a fast end-to-end smoke test:

1. Login
   - Web: login as HR head, recruiter, and interviewer.
   - Mobile: login as applicant.
2. Job creation
   - Recruiter creates or opens a job posting.
   - Recruiter configures requirements and evaluation form.
3. Applicant application
   - Applicant browses jobs, saves a job if desired, uploads/resuses a resume, and applies.
4. AI screening
   - Recruiter runs AI screening for the application.
   - Confirm final score and score components are shown.
   - Confirm AI does not automatically make the final hiring decision.
5. Ranking
   - Recruiter opens ranked candidates for the job.
6. Interview invitation
   - Recruiter assigns an interviewer.
   - Interviewer sends or reviews invitation.
   - Applicant accepts or declines invitation.
7. Transcript and summary
   - Interviewer uploads a recording or uses seeded mock recording data.
   - Generate/review transcript.
   - Generate/review AI summary.
8. Evaluation
   - Interviewer submits evaluation.
   - Recruiter reviews evaluation detail.
9. Hiring decision
   - Recruiter submits hiring recommendation.
   - HR head reviews pending decision and approves/rejects.
10. Offer acceptance
   - Recruiter creates job offer after approval.
   - Applicant accepts or declines the offer.
11. Analytics
   - Review recruiter, interviewer, and HR-head analytics dashboards.
   - Export PDF report if needed.
12. Billing demo flow
   - HR head views plans/subscription/invoices.
   - Use demo payment success flow unless real Stripe credentials are configured.

## Optional Services and Fallback Testing

The FYP demo should work without real external service credentials:

- AI semantic matching may fall back to local lexical scoring if semantic model dependencies are unavailable.
- Transcription may use mock/demo fallback without external ASR credentials.
- AI summaries may use mock/demo fallback without external LLM credentials.
- Email uses the console backend locally.
- Calendar integration should remain disabled unless explicitly implemented/configured.
- Payment should use demo mode unless valid Stripe/payment gateway credentials are configured.

Tests should not call real external APIs. Any future integration tests should mock SendGrid, Google Calendar, Stripe/PayPal/FPX, OpenAI, Whisper, or other third-party services.

## Recommended Pre-Demo Test Sequence

Run these commands before an examiner demo:

```bash
cd backend
python manage.py check
python manage.py test apps.users.tests_seed_demo_data
python manage.py migrate
python manage.py seed_demo_data
```

Then verify the web and mobile clients:

```bash
cd ../web
npm run build

cd ../mobile
flutter analyze
```
