# HRRecruit

## Final recruitment workflow

The final decision is made through a **job-level Hiring Decision**, not an applicant-level decision:

`Job open → applicants apply → AI screening/ranking → recruiter shortlists → recruiter closes application intake → interviews → evaluations → Ready for Hiring Decision → recruiter compares applicants and submits Recommend Hire or Recommend No Hire → Hiring Manager approves/rejects → recruiter sends approved offers → applicant accepts/declines`

Closing application intake prevents new applications while preserving every existing application for interviews, evaluation, comparison, and human review. Recommend Hire may select up to the job's vacancy count. Recommend No Hire selects nobody and requires a justification. Applicants never see internal decision or HR review details and are notified only when an approved offer is actually sent.

HRRecruit is a Final Year Project (FYP) recruitment management SaaS prototype. It combines a Django REST Framework backend, a React web portal, and a Flutter applicant mobile app to support the recruitment workflow from job posting to application screening, interviews, hiring approval, offers, notifications, analytics, and subscription demo flows.

The project is designed for examiner review and FYP demonstration. It includes implemented business flows and local/demo fallbacks for external integrations so the system can be demonstrated without paid third-party services.

## Problem Statement

Recruitment teams often manage job postings, applications, interview feedback, hiring approvals, and applicant communication across separate tools. This can make applicant tracking slow, inconsistent, and difficult to audit.

HRRecruit addresses this by providing one role-based platform where:

- Applicants can find jobs, apply, upload resumes, track applications, respond to interviews, and handle job offers.
- Recruiters can create jobs, screen applications, use AI-assisted ranking, schedule interviews, recommend hiring decisions, and create offers.
- Interviewers can review assigned applicants, manage interview invitations, upload recordings, review transcripts/summaries, and submit evaluations.
- Hiring managers can manage the organization, team members, approvals, analytics, and subscription/demo billing.

## User Roles

| Role | Main Responsibilities |
| --- | --- |
| Hiring Manager | Manage organization profile, team members, pending hiring approvals, analytics, reports, and billing/subscription status. |
| Recruiter | Create and manage jobs, configure requirements and evaluation scorecards, review automatically screened applications, rank applicants, assign interviewers, submit hiring decisions, and create job offers. |
| Interviewer | View assigned interviews/applicants, send or review invitations, upload interview recordings, generate/review transcripts and AI summaries, and submit evaluations. |
| Applicant | Register/login through the mobile workflow, manage profile/resume, browse and save jobs, apply, track application status, view notifications/interview invitations/offers, and accept or decline offers. |

## Main Modules

### Implemented modules

- Authentication and role-based access control using JWT.
- User profile and applicant resume upload.
- Organization profile and organization member management.
- Job posting, job detail, duplication, requirements, evaluation scorecard, saved jobs, and job application flow.
- Application management with status history, remarks, shortlisting, rejection, applicant profile, and automatic AI screening on application submission.
- Applicant ranking by job.
- Interview assignment, interview invitation, invitation response, and assigned-interview views.
- Interview recording upload, transcript generation, AI summary generation, and summary editing.
- Interview evaluation submission and detail review.
- Hiring decision submission, hiring manager approval/rejection, job offer creation, and applicant offer response.
- Notifications and unread-count/read-state APIs.
- Role dashboards, analytics endpoints, and PDF report exports.
- Billing plans, current subscription, invoices, demo payment success flow, and optional Stripe checkout/webhook endpoints.

### Demo/fallback modules

- AI resume screening follows the documented weighted scoring algorithm and keeps human decision-making in recruiter/HR workflows.
- Semantic matching can fall back to local lexical scoring if optional semantic model dependencies are not available.
- Interview transcription can run in demo/fallback mode when no external ASR/LLM credentials are configured.
- AI summary generation can run in mock/demo mode when no LLM credentials are configured.
- Interview AI summaries support Google Gemini by setting `USE_REAL_SUMMARY=True`, `SUMMARY_PROVIDER=gemini`, `GEMINI_API_KEY`, and a Gemini `SUMMARY_MODEL` such as `gemini-3.5-flash`; mock/demo summary remains available when real summary is disabled.
- Email currently uses the Django console email backend for local/demo workflows.
- Payment uses a demo flow unless valid Stripe credentials are configured.
- Stripe sandbox checkout requires a test-mode secret key (`sk_test_...`) and webhook signing secret (`whsec_...`). Configure the success/cancel URLs in `backend/.env`, then forward local test events with `stripe listen --forward-to localhost:8000/api/billing/webhooks/stripe/`. The hosted Checkout integration does not require a publishable key in the web application.
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
web/       React web portal for hiring manager, recruiter, and interviewer roles
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
| Hiring Manager | demo.hrhead@example.com |
| Recruiter | demo.recruiter@example.com |
| Interviewer | demo.interviewer@example.com |
| Applicant | demo.applicant@example.com |

All seeded records are fake and intended only for FYP demonstration.

## Important Notes for Examiners

- HRRecruit is an FYP prototype, not a production SaaS deployment.
- The implemented AI assists screening, ranking, transcription, and summaries; underqualified applicants are rejected by the screening threshold, while qualified applicants still require recruiter and HR review before hiring.
- Demo/fallback behavior is intentional so the project can be reviewed without real SendGrid, Google Calendar, payment gateway, OpenAI, Whisper, or other external-service credentials.
- Optional integrations should remain disabled unless valid credentials and a suitable deployment environment are configured.

## Role-Based Applicant Search

HRRecruit provides a protected applicant search API and web portal screens for internal hiring roles. The endpoint is `GET /api/applications/search/` and the backend derives the allowed search scope from the authenticated user's role; the frontend does not decide access by itself.

- Recruiters can search applications for job postings they created within their active organization. Supported safe filters include applicant/job text search, application status, job id, skills, education, experience, AI score range, application/interview dates, and sorting.
- Interviewers can search only applicants assigned to them directly, through interviews, or through interview scheduling requests. Their filters focus on applicant/job text, application status, interview status such as upcoming/completed/pending evaluation, and date range.
- hiring managers can search all applications inside their own organization for oversight. They can filter by applicant/job text, department, recruiter id, application status, hiring decision status, pending hiring manager approval, AI score range, and dates.
- Applicants cannot use applicant search and cannot browse other applicants.

Web portal entry points:

- Recruiter: **Applicant Search** (`/recruiter/applicant-search`)
- Interviewer: **Applicant Search** (`/interviewer/applicant-search`)
- hiring manager: **Applicant Search** (`/hiring-manager/applicant-search`)

## Interview weekly availability scheduling

Interview scheduling now uses reusable weekly availability patterns instead of requiring interviewers to repeatedly create date-specific slots.

1. Interviewers open **My Weekly Availability** and create patterns with weekday, start time, end time, slot duration, mode, meeting link/location, and effective dates.
2. Interviewers can add unavailable dates for holidays, leave, or other exceptions.
3. When a recruiter creates a self-scheduling request for a shortlisted applicant, the applicant sees generated real dates/times from the assigned interviewer's active weekly patterns.
4. Generated slots are hidden when they are in the past, fall on an unavailable date, or match an existing active interview booking for the same interviewer/date/start/end time.
5. Applicants book a real generated slot. The interview stores the actual interview date, start time, end time, mode, and meeting details, and the database constraint prevents duplicate active bookings for the same interviewer and exact time window.
6. Legacy date-specific availability slots remain supported for existing workflows, but weekly patterns are the preferred scheduling workflow.

## Resume Content Validation

HRRecruit validates uploaded resume content before AI-assisted screening. This validation does **not** use a separate ML/AI model. It reuses local PDF/DOCX text extraction, deterministic keyword/regex checks, and the existing skill extraction utility.

A resume is considered ready for screening only when extracted text contains:

- Skills, detected through the existing skill extractor plus deterministic skill keyword matching.
- Education evidence, such as Diploma, Degree, Bachelor, Master, PhD, University, College, CGPA, Computer Science, Information Technology, Accounting, Business, or related education keywords.
- At least one experience-evidence category: work experience, internship experience, or projects. Project details are accepted for fresh graduates.

If text extraction fails, extracted text is empty/too short, or required sections are missing, HRRecruit stores and returns a structured `resume_validation_result` explaining missing fields and warnings. Invalid resumes do not receive AI screening scores until the applicant uploads a corrected resume.

## Speaker-separated interview transcription

HRRecruit keeps interview transcription local/offline-friendly by default. Whisper performs speech-to-text transcription and, when available, returns timestamped transcript segments. Speaker diarization is a separate optional step that detects who spoke when. HRRecruit aligns Whisper segments with diarization speaker turns using timestamp overlap and preserves real diarizer ids such as `SPEAKER_00`; it never infers `Interviewer` or `Applicant` labels.

Storage follows the interview ERD flow: `Interview` → `InterviewRecording` → `InterviewTranscript` → `InterviewAISummary`. The uploaded audio stays on `InterviewRecording.audio_file`. `InterviewTranscript.transcript_text` stores the readable transcript, using speaker labels when speaker separation succeeds. `InterviewTranscript.transcript_json` stores metadata including `plain_transcript`, `speaker_labelled_transcript`, `diarization_status`, `diarization_warning`, and structured speaker `segments`.

If optional diarization dependencies are not installed or configured, HRRecruit falls back to the existing plain transcript behavior and saves a clear diarization status such as `not_configured`, `unavailable`, or `failed` with a warning. Full local diarization can be enabled later by installing optional diarization packages such as `pyannote.audio`, accepting any required local model terms, and setting `USE_SPEAKER_DIARIZATION=True` plus the required local/model token configuration. No paid external API is required for the fallback path. For development environments that must require real speaker separation, set `REQUIRE_SPEAKER_DIARIZATION=True`; transcript generation will then return an error instead of saving a plain-transcript fallback when diarization does not complete.

If the transcript metadata shows a Hugging Face `GatedRepoError` or `403 Client Error`, the backend token is valid syntactically but the Hugging Face account has not been granted access to the gated pyannote model files being downloaded. Log in to Hugging Face with the account that owns `PYANNOTE_AUTH_TOKEN`, open the model page named in the warning, accept/request access, then create/use a read token from that same account and restart Django. Newer pyannote versions may download `pyannote/speaker-diarization-community-1`, so that model's access conditions may also need to be accepted even when `DIARIZATION_MODEL` is set to `pyannote/speaker-diarization-3.1`.

## Real interview transcription

HRRecruit uses a **real result or clear failure** policy for interview AI. Set `STRICT_REAL_AI=True` and `ALLOW_MOCK_AI=False`; no transcript, speaker label, or AI summary is synthesized when a provider fails. A failed job is retained with `FAILED` and its real error message.

Configure `WHISPER_MODEL_SIZE` as `tiny`, `base`, `small`, `medium`, or `large` (smaller real models are faster). Audio is converted with `ffmpeg` to 16 kHz mono WAV before local Whisper runs, and loaded Whisper models are cached per process. CUDA is selected automatically when PyTorch reports an available GPU. This implementation uses `openai-whisper`, not faster-whisper.

Set `ENABLE_SPEAKER_DIARIZATION=True` only after installing/configuring `pyannote.audio`, accepting the selected model terms, and setting `PYANNOTE_AUTH_TOKEN`. When disabled, the UI says separation is disabled. When it fails, the plain real transcript remains available and the diarization status/error is explicit; it never invents Interviewer or Applicant labels.
