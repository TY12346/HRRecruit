# HRRecruit Demo Guide

This guide summarizes how to prepare and present the HRRecruit FYP demo. For the full scripted walkthrough and backup plan, also read [`FINAL_DEMO_SCRIPT.md`](FINAL_DEMO_SCRIPT.md).

All demo data is fake and intended only for project demonstration.

## 1. Demo Preparation

### Start PostgreSQL

Ensure PostgreSQL is running and the configured database exists. The default expected database is:

```text
hrrecruit_db
```

### Migrate and seed backend data

From the repository root:

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py seed_demo_data
```

The seed command is safe to run multiple times. It creates/updates fake demo accounts, organization data, job postings, application data, AI screening scores, interview transcript/summary data, evaluation data, hiring approval data, notifications, and billing demo records.

If only the first HR-head account is needed, this command is also available:

```bash
python manage.py bootstrap_demo_hr_head --email hr-head.demo@hrrecruit.test --password DemoPass123!
```

### Start backend

```bash
python manage.py runserver
```

For a physical mobile device:

```bash
python manage.py runserver 0.0.0.0:8000
```

### Start web portal

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Open the Vite URL, normally:

```text
http://localhost:5173
```

### Start Flutter app

In a third terminal:

```bash
cd mobile
flutter pub get
flutter run
```

Use the Android emulator default API URL `http://10.0.2.2:8000/api/`, or set the physical-device LAN URL in the app/API settings.

## 2. Demo Accounts

All seeded demo users use the same default password:

```text
DemoPass123!
```

| Role | Email | Demo Purpose |
| --- | --- | --- |
| HR Head | demo.hrhead@example.com | Organization, subscription, HR approval, offer oversight, analytics. |
| Recruiter | demo.recruiter@example.com | Job posting, candidate screening, candidate ranking, interview setup, hiring recommendation, offer creation. |
| Interviewer | demo.interviewer@example.com | Assigned interviews, invitation workflow, transcript/summary review, evaluation submission. |
| Applicant | demo.applicant@example.com | Job search/application, notifications, interview invitation response, job offer response. |

To change the seeded password for all demo users:

```bash
python manage.py seed_demo_data --password 'AnotherValidPass123!'
```

To refresh demo data without changing existing demo passwords:

```bash
python manage.py seed_demo_data --no-update-password
```

## 3. Suggested Demo Order

Follow this order for a clear examiner walkthrough:

1. HR head overview
   - Show organization profile, dashboard, team members, subscription/billing area, and analytics overview.
2. Recruiter job setup
   - Login as recruiter.
   - Show job list/detail, job requirements, and evaluation form builder.
3. Applicant application
   - Login as applicant in the mobile app.
   - Show job search, saved jobs if needed, profile/resume, and application status.
4. AI screening
   - Return to recruiter.
   - Open an application and show AI-assisted screening score components.
   - Explain that AI supports recruiter review and does not automatically reject/hire.
5. Candidate ranking
   - Show ranked candidates for a job.
6. Interview invitation
   - Assign interviewer and show interview invitation flow.
   - Show applicant invitation response where appropriate.
7. Transcript and AI summary
   - Login as interviewer.
   - Show recording/transcript page and AI summary page.
   - Explain mock/fallback behavior for demo mode.
8. Evaluation submission
   - Submit or review interviewer evaluation.
9. Hiring decision and HR approval
   - Recruiter submits recommendation.
   - HR head approves or rejects the pending hiring decision.
10. Job offer and applicant response
    - Recruiter creates an offer after approval.
    - Applicant accepts or declines in the mobile app.
11. Analytics/PDF report
    - Show role dashboards and PDF report export.
12. Billing demo
    - Show plans, current subscription, invoice/demo payment record, and explain demo payment behavior.

## 4. External Integration Demo Notes

The FYP demo is designed to work without real external services:

- Email: console email backend/local OTP behavior.
- AI resume screening: local algorithm with fallback semantic matching.
- Transcription: mock/demo fallback when no external ASR key is configured.
- AI summary: mock/demo fallback when no LLM key is configured.
- Calendar: not enabled by default; treat as optional/future integration unless explicitly configured.
- Payment: demo payment/subscription flow unless valid Stripe credentials are configured.

Do not claim SendGrid, Google Calendar, Stripe/PayPal/FPX, OpenAI, Whisper, or similar services are fully enabled unless valid credentials and environment settings are configured and tested.

## 5. Backup Plan

Use [`FINAL_DEMO_SCRIPT.md`](FINAL_DEMO_SCRIPT.md) as the primary backup-plan reference. Recommended backup actions:

- If live application creation fails, use seeded Software Engineer demo records.
- If optional AI services fail, show stored seeded screening/transcript/summary data and explain fallback behavior.
- If mobile networking fails on a physical device, switch to Android emulator or show API/web-side data.
- If payment checkout fails, use the demo payment success/subscription records.
- If PDF export fails due to environment dependency issues, show dashboard analytics and mention ReportLab/backend requirement.

## 6. Quick Smoke Test Before Demo

```bash
cd backend
python manage.py test apps.users.tests_seed_demo_data
```

Then manually verify login for all four demo accounts before the presentation starts.
