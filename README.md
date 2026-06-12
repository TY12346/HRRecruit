# HRRecruit

HRRecruit is a Final Year Project (FYP) recruitment management SaaS prototype. It combines a Django REST Framework backend, a React web portal, and a Flutter applicant mobile app to support the recruitment workflow from job posting to application screening, interviews, hiring approval, offers, notifications, analytics, and subscription demo flows.

The project is designed for examiner review and FYP demonstration. It includes implemented business flows and local/demo fallbacks for external integrations so the system can be demonstrated without paid third-party services.

## Problem Statement

Recruitment teams often manage job postings, applications, interview feedback, hiring approvals, and applicant communication across separate tools. This can make candidate tracking slow, inconsistent, and difficult to audit.

HRRecruit addresses this by providing one role-based platform where:

- Applicants can find jobs, apply, upload resumes, track applications, respond to interviews, and handle job offers.
- Recruiters can create jobs, screen applications, use AI-assisted ranking, schedule interviews, recommend hiring decisions, and create offers.
- Interviewers can review assigned candidates, manage interview invitations, upload recordings, review transcripts/summaries, and submit evaluations.
- HR heads can manage the organization, team members, approvals, analytics, and subscription/demo billing.

## User Roles

| Role | Main Responsibilities |
| --- | --- |
| HR head | Manage organization profile, team members, pending hiring approvals, analytics, reports, and billing/subscription status. |
| Recruiter | Create and manage jobs, configure requirements and evaluation forms, review automatically screened applications, rank candidates, assign interviewers, submit hiring recommendations, and create job offers. |
| Interviewer | View assigned interviews/candidates, send or review invitations, upload interview recordings, generate/review transcripts and AI summaries, and submit evaluations. |
| Applicant | Register/login through the mobile workflow, manage profile/resume, browse and save jobs, apply, track application status, view notifications/interview invitations/offers, and accept or decline offers. |

## Main Modules

### Implemented modules

- Authentication and role-based access control using JWT.
- User profile and applicant resume upload.
- Organization profile and organization member management.
- Job posting, job detail, duplication, requirements, evaluation form, saved jobs, and job application flow.
- Application management with status history, remarks, shortlisting, rejection, candidate profile, and automatic AI screening on application submission.
- Candidate ranking by job.
- Interview assignment, interview invitation, invitation response, and assigned-interview views.
- Interview recording upload, transcript generation, AI summary generation, and summary editing.
- Interview evaluation submission and detail review.
- Hiring decision submission, HR-head approval/rejection, job offer creation, and applicant offer response.
- Notifications and unread-count/read-state APIs.
- Role dashboards, analytics endpoints, and PDF report exports.
- Billing plans, current subscription, invoices, demo payment success flow, and optional Stripe checkout/webhook endpoints.

### Demo/fallback modules

- AI resume screening follows the documented weighted scoring algorithm and keeps human decision-making in recruiter/HR workflows.
- Semantic matching can fall back to local lexical scoring if optional semantic model dependencies are not available.
- Interview transcription can run in demo/fallback mode when no external ASR/LLM credentials are configured.
- AI summary generation can run in mock/demo mode when no LLM credentials are configured.
- Email currently uses the Django console email backend for local/demo workflows.
- Payment uses a demo flow unless valid Stripe credentials are configured.
- Calendar integration is not enabled by default and should be treated as optional/future integration unless credentials and code support are explicitly configured.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Backend API | Django, Django REST Framework |
| Database | PostgreSQL |
| Web portal | React, Vite, Material UI |
| Applicant mobile app | Flutter |
| Authentication | JWT via `djangorestframework-simplejwt` |
| AI service layer | Local service files under `backend/apps/ai_services/` with fallback/demo behavior |
| Reports | ReportLab PDF generation |
| Local files | Django local media storage |

## Repository Structure

```text
backend/   Django REST Framework API and management commands
web/       React web portal for HR head, recruiter, and interviewer roles
mobile/    Flutter mobile app for applicants
docs       Project-level Markdown documentation in the repository root
```

## Documentation Index

- [Setup Guide](SETUP_GUIDE.md) - local environment setup for backend, web, mobile, PostgreSQL, and demo data.
- [API Documentation](API_DOCUMENTATION.md) - high-level API groups, confirmed example endpoints, roles, and permission notes.
- [Testing Guide](TESTING_GUIDE.md) - backend, React, Flutter, and manual smoke testing commands.
- [Demo Guide](DEMO_GUIDE.md) - FYP demonstration preparation, accounts, demo flow, and backup plan references.
- [Deployment Notes](DEPLOYMENT_NOTES.md) - local/demo deployment assumptions and production considerations.
- [Known Limitations](KNOWN_LIMITATIONS.md) - honest implementation limitations and future enhancements.
- [Algorithm Specification](ALGORITHMS.md) - AI scoring and supporting algorithm rules.
- [Final Demo Script](FINAL_DEMO_SCRIPT.md) - detailed scripted demo path and backup plan.
- [Final System Gap Report](FINAL_SYSTEM_GAP_REPORT.md) - implementation status and remaining gaps.
- [AI Algorithm Validation Report](AI_ALGORITHM_VALIDATION_REPORT.md) - algorithm validation notes.

## Quick Local Demo Start

The detailed steps are in the setup and demo guides. A typical local workflow is:

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver

# Web portal
cd ../web
npm install
npm run dev

# Mobile app
cd ../mobile
flutter pub get
flutter run
```

PostgreSQL must be running before backend migration, seeding, or tests. Configure `backend/.env` with the database connection values before running backend commands.

## Demo Accounts

After running `python manage.py seed_demo_data` from the `backend/` directory, the seeded demo password is:

```text
DemoPass123!
```

| Role | Email |
| --- | --- |
| HR Head | demo.hrhead@example.com |
| Recruiter | demo.recruiter@example.com |
| Interviewer | demo.interviewer@example.com |
| Applicant | demo.applicant@example.com |

All seeded records are fake and intended only for FYP demonstration.

## Important Notes for Examiners

- HRRecruit is an FYP prototype, not a production SaaS deployment.
- The implemented AI assists screening, ranking, transcription, and summaries; it does not automatically make final hiring decisions.
- Demo/fallback behavior is intentional so the project can be reviewed without real SendGrid, Google Calendar, payment gateway, OpenAI, Whisper, or other external-service credentials.
- Optional integrations should remain disabled unless valid credentials and a suitable deployment environment are configured.
