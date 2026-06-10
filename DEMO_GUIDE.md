# HRRecruit Demo Guide

All demo data in this guide is fake and is intended only for the HRRecruit FYP demonstration.

## Demo seed command

From the backend directory, run:

```bash
python manage.py migrate
python manage.py seed_demo_data
```

The seed command is safe to run multiple times. It uses existing records where possible, updates the known demo records, and does not delete or reset real data.

## Demo account credentials

All seeded demo users use the same default password:

```text
DemoPass123!
```

| Role | Email | Purpose |
| --- | --- | --- |
| HR Head | demo.hrhead@example.com | Organization, subscription, HR approval, offer oversight |
| Recruiter | demo.recruiter@example.com | Job posting, candidate screening, interview setup, hiring recommendation |
| Interviewer | demo.interviewer@example.com | Interview assignment, transcript/summary review, interview evaluation |
| Applicant | demo.applicant@example.com | Application status, interview invitation, job offer acceptance |

To change the seeded password for all demo users, run:

```bash
python manage.py seed_demo_data --password 'AnotherValidPass123!'
```

To keep existing demo passwords unchanged while refreshing other demo data, run:

```bash
python manage.py seed_demo_data --no-update-password
```

## Expected demo data

The command creates or updates:

- Organization: `TechNova Solutions Sdn Bhd`.
- Active memberships for the HR head, recruiter, and interviewer.
- Open jobs:
  - `Software Engineer` with Python, Django, React, PostgreSQL, REST API, education, and experience requirements.
  - `Data Analyst` with SQL, dashboard reporting, education, and analytics experience requirements.
- Applicant profile for the fake demo applicant.
- A Software Engineer application with mock resume text and stored AI screening scores.
- Interview data showing assignment, invitation acceptance, mock recording placeholder, transcript, AI summary, and interviewer evaluation.
- Hiring data showing recruiter recommendation, HR-head approval, accepted fake offer, and hired application status.
- Notifications for application status, interview invitation, job offer, and hiring decision updates.
- Demo-mode billing data with a Pro monthly subscription and a paid demo payment record.

## Short demo workflow

1. Log in as the HR head and confirm the organization and subscription exist.
2. Log in as the recruiter and review the Software Engineer job and the demo applicant's AI-assisted screening result.
3. Show that AI scores support human review and do not make the final hiring decision.
4. Open the interview workflow to show interviewer assignment and the accepted invitation.
5. Log in as the interviewer and review the transcript, mock AI summary, and evaluation.
6. Return as the recruiter to show the hiring recommendation.
7. Return as the HR head to show the approved recommendation.
8. Log in as the applicant to show application status, notifications, and the accepted fake offer.

## External integration note

The FYP demo seed uses local/mock/demo data only. It does not call SendGrid, Google Calendar, Stripe, PayPal, FPX, OpenAI, Whisper, or any other real external service. Optional real integrations remain disabled unless the project is explicitly configured for them.

## Smoke test command

From the backend directory, run:

```bash
python manage.py test apps.users.tests_seed_demo_data
```

These tests verify that the seed command runs, creates the core demo users, organization, jobs, application, subscription, and remains idempotent for core records.
