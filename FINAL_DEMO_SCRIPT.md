# HRRecruit Final FYP Demo Script

This script is the presenter runbook for the final HRRecruit FYP demonstration. It follows the seeded demo workflow in business order and uses only fake/demo data created by `python manage.py seed_demo_data`.

## 1. Demo Purpose and Presenter Opening Notes

### What HRRecruit solves

HRRecruit is an AI-powered recruitment management SaaS for managing the full hiring lifecycle across web and mobile:

- Applicants search and apply for jobs from the Flutter mobile app.
- Recruiters create jobs, review applications, use AI-assisted resume screening, shortlist candidates, and submit hiring recommendations.
- Interviewers manage assigned interviews, invitations, recordings, transcripts, AI summaries, and evaluation forms.
- HR department heads manage organization oversight, billing, analytics, and final hiring approval.

### Why there are four roles

The four roles demonstrate real recruitment separation of duties:

| Role | Demo responsibility |
| --- | --- |
| HR Head | Organization oversight, team management, billing, analytics, and final decision approval |
| Recruiter | Job setup, candidate screening, shortlisting, interview assignment, and hiring recommendation |
| Interviewer | Interview invitation, transcript/summary review, and evaluation submission |
| Applicant | Job discovery, application, interview invitation response, offer response, and notifications |

### AI and governance message

During the demo, repeat this point clearly: **AI supports human decision-making but does not replace human decisions**. AI can extract resume information, calculate matching scores, generate candidate ranking support, transcribe interview content, and draft interview summaries. The recruiter still shortlists/rejects applicants, the interviewer still submits evaluation evidence, and the HR head still approves or rejects the final hiring decision.

### Resume scoring formula

The AI resume screening score uses the documented weighted formula:

```text
final_score = 0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score
```

In the seeded Software Engineer demo application:

| Score component | Seeded value |
| --- | ---: |
| Semantic score | 82.00 |
| Skill score | 88.00 |
| Experience score | 78.00 |
| Education score | 85.00 |
| Final score | 83.30 |

The score explains fit and ranking, but the final shortlist/hire/reject actions remain human-controlled.

### Interview summary message

The AI interview summary helps the interviewer quickly review conversation evidence. The required summary fields are:

- `strengths`
- `weaknesses`
- `communication_score`
- `overall_impression`
- `editable_summary_text`

The interviewer can edit the summary before submitting the evaluation, so the final evaluation remains the interviewer's responsibility.

### HR-head control message

The HR head is the final governance checkpoint. Even after a recruiter recommends hiring, the job offer should only proceed after HR-head approval.

## 2. Preparation Checklist

> Recommended browser setup: use one normal browser window for the web portal, an incognito/private window or second browser profile for switching web roles quickly, and the Flutter emulator/device for the applicant.

### 2.1 Start PostgreSQL

Use the command appropriate for your environment:

```bash
# Linux system service example
sudo systemctl start postgresql

# macOS Homebrew example
brew services start postgresql

# Docker example, if your local setup uses Docker
# docker compose up -d db
```

Expected result: PostgreSQL is running and the backend can connect using the local `.env` database settings.

Backup note: If PostgreSQL is not running or credentials are wrong, start the service, verify `.env`, then rerun migrations and the seed command.

### 2.2 Activate backend virtual environment

From the repository root:

```bash
cd backend
source .venv/bin/activate
```

If your virtual environment is named differently, activate the correct environment, for example `source venv/bin/activate` on Linux/macOS or `.venv\Scripts\activate` on Windows PowerShell.

Expected result: the terminal prompt shows the backend virtual environment and `python manage.py --help` works.

Backup note: If dependencies are missing, run `pip install -r requirements.txt` in the backend virtual environment.

### 2.3 Run migrations

```bash
cd backend
python manage.py migrate
```

Expected result: all migrations apply successfully or Django reports no migrations to apply.

Backup note: If migrations fail because PostgreSQL is unavailable, fix the database connection first and rerun the command.

### 2.4 Seed demo data

```bash
cd backend
python manage.py seed_demo_data
```

Expected result: the command prints `Demo seed data created/updated successfully.`, demo credentials, `TechNova Solutions Sdn Bhd`, and seeded jobs `Software Engineer` and `Data Analyst`.

The seed command is idempotent. It updates known fake demo records and does not delete existing data.

Backup note: If duplicate or stale demo data appears, rerun `python manage.py seed_demo_data`. If a custom password was previously used, either run the command without `--no-update-password` to reset all demo users to the default password or run `python manage.py seed_demo_data --password 'YourPasswordHere'` and use that password.

### 2.5 Optional smoke test for seed data

```bash
cd backend
python manage.py test apps.users.tests_seed_demo_data
```

Expected result: seed-data tests pass and confirm core demo records are created idempotently.

Backup note: If this test fails because the local test database cannot be created, continue only if manual login and seeded records work; mention the environment limitation if asked.

### 2.6 Start Django backend server

For Android emulator and local web portal:

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

Expected result: Django serves the API at `http://127.0.0.1:8000/api/` and is reachable from the Android emulator at `http://10.0.2.2:8000/api/`.

Backup note: If port `8000` is already used, stop the other process or use another port and update the web/mobile API base URLs.

### 2.7 Start React web portal

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Expected result: Vite starts the React web portal, commonly at `http://localhost:5173/`.

Backup note: If dependencies are already installed, `npm install` can be skipped. If `npm install` fails because network access is unavailable, use an environment where `node_modules` already exists or restore cached dependencies.

### 2.8 Start Flutter mobile app or emulator

In a third terminal:

```bash
cd mobile
flutter pub get
flutter run
```

Expected result: the Flutter applicant app opens on an emulator/device. The default Android emulator API URL is `http://10.0.2.2:8000/api/`.

For a physical phone, start Django on `0.0.0.0:8000`, ensure firewall access, and set the mobile app API URL to:

```text
http://YOUR_COMPUTER_LAN_IP:8000/api/
```

Backup note: If the emulator/device is not ready, demonstrate applicant API-related screens using screenshots, a pre-recorded run, or browser API responses while explaining the intended mobile flow.

### 2.9 Confirm demo accounts can log in

Use the web portal for HR head, recruiter, and interviewer. Use the Flutter mobile app for applicant.

Expected result: each role reaches its own dashboard/home screen and cannot access other roles' protected pages.

Backup note: If any login fails, rerun `python manage.py seed_demo_data` to reset demo passwords to `DemoPass123!`.

## 3. Demo Accounts and Seeded Demo Data

### 3.1 Demo credentials

All seeded demo users use this default password unless the seed command is run with `--password`:

```text
DemoPass123!
```

| Role | Email | Password | Use in demo |
| --- | --- | --- | --- |
| HR Head | `demo.hrhead@example.com` | `DemoPass123!` | Organization, team, billing, analytics, final approval |
| Recruiter | `demo.recruiter@example.com` | `DemoPass123!` | Jobs, applications, AI screening, ranking, shortlisting, hiring recommendation |
| Interviewer | `demo.interviewer@example.com` | `DemoPass123!` | Assigned interviews, invitations, transcript, AI summary, evaluation |
| Applicant | `demo.applicant@example.com` | `DemoPass123!` | Mobile job discovery, application status, interview invitation, job offer, notifications |

### 3.2 Seeded records to mention

| Record type | Seeded demo values |
| --- | --- |
| Organization | `TechNova Solutions Sdn Bhd` |
| Organization registration | `DEMO-TN-001` |
| Open jobs | `Software Engineer`, `Data Analyst` |
| Main demo job | `Software Engineer` |
| Software Engineer requirements | Python, Django, React, PostgreSQL, REST API; Bachelor in Computer Science or related field; at least 2 years of development experience; communication/teamwork |
| Evaluation criteria | Technical fit, Communication, Culture and teamwork, Learning agility |
| Applicant profile | Demo applicant with Django, React, PostgreSQL, REST API, analytics dashboard experience |
| Interview meeting link | `https://meet.example.com/hrrecruit-demo-software-engineer` |
| Billing | Demo Pro monthly subscription, MYR 299.00, paid demo payment reference `DEMO-SEED-PAYMENT` |

## 4. Full Demo Flow in Correct Business Order

Each step includes actor/role, page or app screen, action, expected result, and backup note.

### A. HR Head Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| A1 | HR Head | Web `/login` | Log in with `demo.hrhead@example.com` / `DemoPass123!`. | HR head is redirected to the HR-head dashboard. | If login fails, rerun `python manage.py seed_demo_data` and retry. |
| A2 | HR Head | Web `/hr-head` dashboard | View high-level organization/dashboard cards. | Dashboard loads organization-level recruitment overview for TechNova. | If analytics cards are sparse, explain this depends on seeded demo workflow volume. |
| A3 | HR Head | Web `/hr-head/organization` | Open organization profile. | Organization shows `TechNova Solutions Sdn Bhd` with active status/details. | If page fails, mention the seed created the organization and show Team/Billing as backup evidence. |
| A4 | HR Head | Web `/hr-head/team` | Confirm HR head, recruiter, and interviewer accounts. | Team members include Demo HR Head, Demo Recruiter, and Demo Interviewer with active memberships. | If duplicated local data appears, point out the known demo accounts by email. |
| A5 | HR Head | Web `/hr-head/billing` | View subscription/billing status. | Active Pro monthly subscription and demo payment status are visible if billing data loads. | If billing API/page fails, explain demo payment data is seeded and real gateways are disabled. |
| A6 | HR Head | Web `/hr-head/analytics` | View analytics if demo data exists. | Organization analytics display seeded pipeline metrics where available. | If charts are empty, explain limited seeded data may only show one completed workflow. |

### B. Recruiter Job Setup Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| B1 | Recruiter | Web `/login` | Log in with `demo.recruiter@example.com` / `DemoPass123!`. | Recruiter reaches recruiter dashboard. | Use a separate browser profile/incognito window to avoid role-session confusion. |
| B2 | Recruiter | Web `/recruiter` dashboard | Review dashboard overview. | Recruiter sees job/application workflow entry points. | If metrics are minimal, continue to Jobs and Applications pages. |
| B3 | Recruiter | Web `/recruiter/jobs` | Open the `Software Engineer` job or create a new job only if needed. | Seeded `Software Engineer` and `Data Analyst` jobs are listed as open jobs. | Prefer opening seeded data; do not depend on creating new data during final demo. |
| B4 | Recruiter | Web `/recruiter/jobs/:jobId` | Review Software Engineer posting details. | Job description, location `Kuala Lumpur / Hybrid`, full-time employment, salary around MYR 6500, and open status are visible. | If exact salary is hidden by UI, focus on title/status/description. |
| B5 | Recruiter | Web `/recruiter/jobs/:jobId/requirements` | Review job requirements. | Requirements show skill, education, experience, and other communication/teamwork criteria with weights/thresholds. | If requirements are not visible on this page, mention seeded requirements from the job setup. |
| B6 | Recruiter | Web `/recruiter/jobs/:jobId/evaluation-form` | Review evaluation criteria. | Criteria include Technical fit, Communication, Culture and teamwork, and Learning agility. | If form builder is read-only or incomplete, explain evaluation criteria are seeded and used in the interviewer evaluation step. |
| B7 | Recruiter | Job detail/list | Confirm job status. | `Software Engineer` is open/active and ready for applications. | If status display differs by wording, use the seeded open job as the main demo job. |

### C. Applicant Mobile Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| C1 | Applicant | Flutter Login | Log in with `demo.applicant@example.com` / `DemoPass123!`. | Applicant reaches the mobile home screen. | If API unreachable, verify mobile API settings and Django `runserver 0.0.0.0:8000`. |
| C2 | Applicant | Mobile Home / Find jobs | Tap Find jobs. | Available jobs list loads, including `Software Engineer` and `Data Analyst`. | If the applicant already applied to Software Engineer, use the job detail/application status as evidence. |
| C3 | Applicant | Job details | Open `Software Engineer`. | Job details and requirements are visible. | If already applied, explain the seed data represents a completed application for this job. |
| C4 | Applicant | Job details | Tap Apply for job if available. | A new application is created or the UI indicates the applicant has already applied. | Seeded demo data already includes the Software Engineer application, so “already applied” is acceptable. |
| C5 | Applicant | Profile/Resume or application flow | Upload or confirm resume/application data. | Applicant profile/resume data is available; seeded application contains extracted resume text. | If file picker/emulator file access fails, use the seeded resume/application data and continue. |
| C6 | Applicant | My applications | Open application status. | Software Engineer application status shows the progressed seeded lifecycle, ending in hired/accepted offer if the full seed state is displayed. | If status names differ by UI formatting, explain the lifecycle history from submitted through hired. |

### D. AI Resume Screening Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| D1 | Recruiter | Web `/recruiter/applications` | Open applications for `Software Engineer`. | Demo applicant application is listed. | If filtering is unavailable, open the application directly from the application list. |
| D2 | Recruiter | Candidate/application detail | Trigger or review AI resume screening. | Seeded screening results are visible without calling real external AI services. | If trigger button is absent or already completed, state the seed command pre-populated screening results for demo reliability. |
| D3 | Recruiter | Candidate/application detail | Show extracted resume fields. | Extracted skills include Python, Django, React, PostgreSQL, REST API; education shows Bachelor/Computer Science; experience shows 2.5 years. | If UI collapses JSON/details, summarize from seeded demo record. |
| D4 | Recruiter | Candidate/application detail | Show component scores. | Semantic score 82.00, skill score 88.00, experience score 78.00, education score 85.00, final score 83.30. | If exact decimals are formatted differently, point out the same weighted components. |
| D5 | Recruiter | Candidate/application detail | Explain formula aloud. | Presenter states `final_score = 0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score`. | Use this script if formula is not shown directly in UI. |
| D6 | Recruiter | Candidate/application detail | Explain AI governance. | Audience understands AI does not auto-reject or auto-hire; recruiter makes shortlist/reject decisions. | If application is already hired from seed data, explain this reflects a completed workflow while decisions were still human-approved. |

### E. Candidate Ranking and Shortlisting Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| E1 | Recruiter | Web `/recruiter/jobs/:jobId/ranking` | Open candidate ranking page for Software Engineer. | Ranked candidate list appears, with demo applicant ranked using AI-assisted scores. | If only one candidate is shown, explain ranking still demonstrates score-based ordering. |
| E2 | Recruiter | Candidate ranking | Review ranked candidates. | Demo applicant shows strong fit based on final score and extracted criteria. | If ranking page fails, show application detail AI score as fallback. |
| E3 | Recruiter | Candidate/application detail | Shortlist suitable candidate or show existing shortlisted history. | Candidate is shortlisted or seeded stage history shows recruiter shortlisted candidate for interview. | If status is already later than shortlisted, explain the seed data has completed the workflow. |
| E4 | Recruiter | Web `/recruiter/applications/:applicationId/assign-interview` | Assign interviewer or confirm existing assignment. | Demo Interviewer is assigned to the Software Engineer application/interview. | If assignment already exists, show the assigned interviewer field and proceed. |

### F. Interview Invitation Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| F1 | Interviewer | Web `/login` | Log in with `demo.interviewer@example.com` / `DemoPass123!`. | Interviewer reaches interviewer dashboard. | Use a separate browser profile/incognito window. |
| F2 | Interviewer | Web `/interviewer/interviews` | Open assigned interview. | Software Engineer interview for Demo Applicant appears. | If list is empty, open Assigned candidates and navigate from there. |
| F3 | Interviewer | Web `/interviewer/interviews/:interviewId/invitation` | Send interview invitation or review sent invitation. | Invitation status is sent/accepted; meeting link is available. | Seeded invitation is already accepted for demo continuity. |
| F4 | Applicant | Mobile Interview invitations | Open interview invitation. | Invitation for Software Engineer is visible, with accepted status if seed data is already complete. | If invitation is already accepted, explain applicant accepted it in the seeded lifecycle. |
| F5 | Applicant | Mobile invitation detail | Accept invitation if available. | Interview status updates to scheduled/accepted. | If already accepted, show accepted status and continue. |
| F6 | Interviewer/Recruiter | Web interview detail | Confirm status update. | Interview status/history reflects invitation accepted and interview scheduled/completed in seed data. | If status is already completed, explain the seed includes a completed interview for the later evaluation flow. |

### G. Interview Evaluation and AI Summary Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| G1 | Interviewer | Web `/interviewer/interviews/:interviewId/recording` | Upload/select interview recording or review demo recording. | Demo placeholder recording `demo-interview-placeholder.mp3` exists or upload UI is available. | If upload is unavailable, use seeded placeholder recording. |
| G2 | Interviewer | Recording/transcript page | Generate or review transcript. | Mock transcript shows interviewer/candidate discussion about Django, REST APIs, PostgreSQL, and React collaboration. | If generation button is absent, state seed data preloads mock transcript. |
| G3 | Interviewer | Web `/interviewer/interviews/:interviewId/transcript-summary` | Generate or review AI summary. | AI summary is visible using mock/fallback data. | If real provider is unavailable, explain fallback summary is intentional. |
| G4 | Interviewer | Transcript summary | Show required fields. | Fields shown or explained: strengths, weaknesses, communication_score, overall_impression, editable_summary_text. | If UI labels differ, map displayed fields to these required fields verbally. |
| G5 | Interviewer | Transcript summary | Edit summary if needed. | Editable summary can be adjusted by interviewer before evaluation. | If already saved, explain editable summary exists to keep interviewer in control. |
| G6 | Interviewer | Web `/interviewer/interviews/:interviewId/evaluation` | Submit or review evaluation. | Evaluation criteria scores and total score around 84.00 are present; overall comment recommends hire for demo workflow. | If already submitted, show submitted evaluation as completed evidence. |

### H. Hiring Decision Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| H1 | Recruiter | Web `/recruiter/hiring-decisions` or application hiring-decision page | Open hiring decision page. | Evaluated Software Engineer candidate is available for decision review. | If already decided, show existing decision record. |
| H2 | Recruiter | Hiring decision page | Select only evaluated candidate. | Candidate can be considered because evaluation has been submitted. | If selection is locked by completed seed state, explain the rule: only evaluated candidates should proceed. |
| H3 | Recruiter | Hiring decision page | Submit hire/reject recommendation or review seeded recommendation. | Recruiter recommendation is `hire` with justification. | If already submitted, show seeded recruiter recommendation. |
| H4 | HR Head | Web `/hr-head/hiring-decisions` | Review pending/approved decision. | HR head sees recruiter recommendation and supporting evidence. | If decision is already approved, explain seed data starts at completed state for final demo reliability. |
| H5 | HR Head | Pending hiring decision detail | Approve or reject decision, or review seeded approval. | Seeded HR-head decision is approved with justification. | If no action button appears because already approved, show approval status. |
| H6 | Recruiter | Web `/recruiter/job-offers` | Send job offer if approved or review seeded offer. | Job offer exists for Software Engineer after HR approval. | If already accepted, explain the applicant completed the final offer step in seed data. |

### I. Job Offer and Final Applicant Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| I1 | Applicant | Mobile Job offers | Open job offers. | Software Engineer fake demo offer is visible. | If list is empty due to local state, reseed data and refresh mobile session. |
| I2 | Applicant | Job offer detail/list | Accept or reject offer if action is available. | If accepted, offer status updates to accepted. | Seeded offer is already accepted; show accepted status if no action is available. |
| I3 | Applicant | My applications/application detail | Confirm final application lifecycle. | Application status is hired according to implemented lifecycle. | If UI uses a different status label, explain final accepted/hired state. |
| I4 | Recruiter/HR Head | Web dashboard/applications/analytics | View updated status. | Recruiter/HR head sees accepted offer/hired status reflected in workflow data. | If dashboard metrics lag, open application or offer detail directly. |

### J. Notifications Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| J1 | Applicant | Mobile Notifications | Show application update notification. | Notification such as `Application shortlisted` is visible. | If already marked read, check all notifications instead of unread only. |
| J2 | Applicant | Mobile Notifications | Show interview invitation notification. | Notification related to interview invitation/acceptance is visible. | If notification wording differs, identify the interview-related notification. |
| J3 | Applicant | Mobile Notifications | Show job offer notification. | Notification such as `Demo job offer accepted` is visible. | If not visible, show Job offers page as backup. |
| J4 | Recruiter | Web `/recruiter/notifications` | Show hiring decision update. | Notification such as `HR approved recommendation` is visible. | If notification has been read, use all notifications/read-all view if available. |
| J5 | HR Head | Web `/hr-head/notifications` | Show offer/hiring update. | Notification such as `Offer accepted` is visible. | If empty, explain notification records are seeded and demonstrate applicant/recruiter notifications. |

### K. Analytics and Reports Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| K1 | Recruiter | Web `/recruiter/analytics` | View recruiter analytics. | Recruiter sees job/application/interview pipeline metrics where available. | If limited charts appear, explain the seed includes one completed workflow and two jobs. |
| K2 | Interviewer | Web `/interviewer/analytics` | View interviewer analytics. | Interviewer sees assigned/completed interview and evaluation-related metrics where available. | If empty, show interview list/evaluation as supporting data. |
| K3 | HR Head | Web `/hr-head/analytics` | View HR-head analytics. | HR head sees organization-level analytics where available. | If charts are sparse, mention seeded sample size is intentionally small. |
| K4 | Any supported web role | Analytics/report export button, if available | Export or download PDF report. | PDF downloads or opens successfully if implemented and configured. | If PDF export is unavailable, explain this optional feature can be shown through analytics pages and note PDF generation is unavailable in the current environment. |

### L. Billing/Subscription Flow

| Step | Actor/role | Page or screen | Action | Expected result | Backup note |
| --- | --- | --- | --- | --- | --- |
| L1 | HR Head | Web `/hr-head/billing` | View subscription plans. | Plans are visible, including the seeded Pro monthly plan. | If plan list is empty, run subscription plan migrations/seeding and rerun demo seed. |
| L2 | HR Head | Billing demo payment action, if available | Demonstrate demo payment flow only. | Payment is simulated using demo gateway logic; no real payment is charged. | If action is unavailable because subscription is already paid, show seeded paid demo payment. |
| L3 | HR Head | Billing page | Explain real gateway status. | Audience understands Stripe/real gateways remain disabled unless configured. | Mention real payment integration is intentionally excluded from the FYP reliability path. |
| L4 | HR Head | Billing page/subscription status | Show subscription after demo payment. | Active Pro monthly subscription and paid demo payment are visible if billing UI supports it. | If status is not visible, cite the seeded Pro subscription and demo payment reference verbally. |

## 5. Demo Mode Explanation

HRRecruit intentionally supports local/mock/demo behavior for FYP demo reliability:

- AI semantic matching may use fallback/mock scoring if Sentence-BERT or `sentence-transformers` is unavailable.
- Resume extraction and scoring data can be pre-seeded so the demo does not depend on external AI services.
- Interview transcription may use a mock transcript fallback instead of a real speech-to-text provider.
- AI summary generation may use a mock summary fallback instead of real LLM/API calls.
- Email delivery may use console/demo behavior instead of SendGrid or another real provider.
- Calendar behavior may use local/demo event records instead of Google Calendar OAuth.
- Payment uses demo payment flow and seeded demo payment records instead of Stripe, PayPal, FPX, or any real gateway.
- These fallback behaviors are intentional: they make the final FYP demo repeatable, safe, and independent of internet/API availability.

## 6. Demo Backup Plan

| Risk | Symptoms | Backup plan |
| --- | --- | --- |
| PostgreSQL not running | `python manage.py migrate` or login fails with database connection error | Start PostgreSQL using your local service/Docker command, verify `.env` credentials, rerun migrations, rerun `python manage.py seed_demo_data`. |
| React dependencies missing | `npm run dev` fails because packages are missing | Run `cd web && npm install`. If network is unavailable, use a machine with cached dependencies or a prepared `node_modules` folder. |
| Flutter emulator/device not ready | `flutter run` cannot find device or mobile app cannot reach API | Start Android Studio emulator, run `flutter devices`, verify API URL. For physical phone, run Django on `0.0.0.0:8000`, configure LAN IP in mobile API settings, and allow firewall access. If still blocked, use screenshots/pre-recorded applicant flow and show backend/web data. |
| AI semantic model unavailable | Semantic model import/download fails or screening cannot run live | Use seeded AI screening results. Explain fallback/mock semantic matching is intentional for FYP demo reliability and avoids external model dependency. |
| Real transcription/summary provider unavailable | Transcript/summary generation cannot call external provider | Use seeded mock transcript and mock AI summary. Explain real providers are disabled unless configured. |
| Payment gateway not configured | Billing cannot call Stripe/PayPal/FPX or real checkout is unavailable | Demonstrate demo payment only and show seeded paid demo payment `DEMO-SEED-PAYMENT`. Explain no real payment is charged. |
| PDF export unavailable | Export button missing or PDF endpoint fails locally | Show analytics dashboards instead. State PDF export is optional/conditional and continue with web analytics evidence. |
| Demo data missing or duplicated | Pages are empty, old password fails, or duplicate-looking records appear | Run `cd backend && python manage.py seed_demo_data` again. It is idempotent and updates known demo records. If a custom password was used, rerun with `--password` or without `--no-update-password` to reset demo credentials. |

## 7. Recommended Closing Script

Use this short closing after completing the workflow:

> HRRecruit demonstrates a complete recruitment lifecycle from job posting to applicant offer acceptance. The system separates responsibilities across applicant, recruiter, interviewer, and HR-head roles. AI helps by extracting resume information, scoring candidate fit, ranking applicants, transcribing interviews, and drafting editable summaries. However, each critical decision remains human-controlled: recruiters shortlist and recommend, interviewers evaluate, and HR heads approve final hiring decisions. Demo-mode fallbacks for AI, transcription, calendar, email, and payment make the FYP demonstration reliable without depending on external paid services.
