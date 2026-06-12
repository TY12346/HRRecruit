# HRRecruit Final FYP Readiness Checklist

This checklist is a final submission and demonstration readiness aid for the HRRecruit Final Year Project. It is based on the repository documentation, current Django backend, React web portal, Flutter applicant app, and the documented known limitations.

## Status legend

| Status | Meaning |
|---|---|
| Complete | Current codebase and/or documentation supports the item. Still run the verification step on the final demo machine. |
| Partial | Some support exists, but there is a known gap, prototype limitation, missing UI coverage, or incomplete end-to-end behavior. |
| Not Implemented | No supported implementation was identified in the current codebase/documentation. |
| Manual Verification Required | The item appears documented or implemented, but it depends on local environment, installed tools, seeded data, or live UI/device behavior that must be confirmed manually before the demo. |

## Pre-demo baseline commands

Run these commands from a clean checkout before using the detailed checklist:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py seed_demo_data
python manage.py test

cd ../web
npm ci
npm run lint
npm run build
npm run dev

cd ../mobile
flutter pub get
flutter analyze
flutter run
```

> Important: PostgreSQL must be running and configured before backend migrations/tests. Flutter checks require a machine with the Flutter SDK installed.

---

## 1. Project Setup

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Repository structure is complete | Complete | Confirm root docs plus `backend/`, `web/`, and `mobile/` directories exist. | `README.md`, `backend/manage.py`, `web/package.json`, `mobile/pubspec.yaml` | Structure matches the FYP architecture: Django backend, React web portal, Flutter mobile app. |
| Backend setup instructions exist | Complete | Read backend setup steps. | `SETUP_GUIDE.md`, `README.md` | Includes virtual environment, dependencies, database, migrations, seed data, and server command. |
| React web setup instructions exist | Complete | Read web setup steps and web README. | `SETUP_GUIDE.md`, `web/README.md` | Web dependencies must still be installed on the final demo machine. |
| Flutter mobile setup instructions exist | Complete | Read mobile setup steps and mobile README. | `SETUP_GUIDE.md`, `mobile/README.md` | Flutter SDK/device availability is environment-dependent. |
| Environment variable documentation exists | Complete | Review the documented environment variables. | `SETUP_GUIDE.md`, `DEPLOYMENT_NOTES.md`, `web/.env.example` | Backend uses `.env`; web uses Vite environment variables; mobile can use Dart define or runtime API settings. |
| PostgreSQL setup is documented | Complete | Check database instructions and backend settings. | `SETUP_GUIDE.md`, `DEPLOYMENT_NOTES.md`, `backend/config/settings.py` | PostgreSQL is required from the start; tests and migrations depend on a running PostgreSQL service. |
| Demo data setup is documented | Complete | Run seed command after migrations. | `python manage.py seed_demo_data`, `FINAL_DEMO_SCRIPT.md`, `DEMO_GUIDE.md` | Seed command is intended for demo/local environments only. |

## 2. Backend Foundation

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Django project runs | Manual Verification Required | Start backend and open an API endpoint. | `cd backend && python manage.py runserver` | Requires installed Python dependencies and PostgreSQL. |
| PostgreSQL is configured | Complete | Inspect Django settings and `.env` documentation. | `backend/config/settings.py`, `SETUP_GUIDE.md` | Uses `django.db.backends.postgresql`; no SQLite fallback is documented for normal operation. |
| Migrations can run | Manual Verification Required | Run migrations on demo database. | `cd backend && python manage.py migrate` | Requires PostgreSQL credentials/service to be available. |
| Backend health check passes with `python manage.py check` | Complete | Run Django check. | `cd backend && python manage.py check` | Verified in this workspace: `System check identified no issues (0 silenced).` |
| Backend tests are documented | Complete | Read test guide and run selected suites. | `TESTING_GUIDE.md`, `python manage.py test` | Full tests require PostgreSQL. |
| Role-based authentication is implemented | Complete | Log in as each role and call protected role endpoints. | `backend/apps/users/models.py`, `backend/apps/users/permissions.py`, API docs | Role values follow required names. |
| JWT authentication is implemented | Complete | Login and inspect access/refresh tokens. | `POST /api/auth/login/`, `backend/config/settings.py` | JWT auth is configured globally through DRF SimpleJWT. |

## 3. User Roles and Authentication

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Applicant registration/login | Complete | Register/login as applicant and fetch profile. | `POST /api/auth/register/`, `POST /api/auth/login/`, mobile login screen | Registration is public and returns JWT tokens. |
| Recruiter login | Complete | Seed demo data and log in with recruiter credentials. | `POST /api/auth/login/`, React `/login` | Demo credentials are documented in demo guide/script after seeding. |
| Interviewer login | Complete | Seed demo data and log in with interviewer credentials. | `POST /api/auth/login/`, React `/login` | Role-specific dashboard should load after login. |
| HR head login | Complete | Seed demo data and log in with HR-head credentials. | `POST /api/auth/login/`, React `/login` | HR-head bootstrap and full seed commands exist. |
| Profile access | Complete | Call profile endpoint with bearer token. | `GET /api/auth/profile/`, `PATCH /api/auth/profile/` | Protected by authentication. |
| Role permissions | Complete | Attempt cross-role actions and confirm 403/404 behavior. | Backend role checks in app views; `TESTING_GUIDE.md` | Major flows enforce role checks; continue manual negative testing before demo. |
| Logout | Complete | Post refresh token to logout and retry protected action with blacklisted refresh flow. | `POST /api/auth/logout/` | Access token remains valid until expiry; refresh token blacklist is used. |
| Password reset if implemented | Partial | Exercise OTP request/confirm endpoints; confirm UI availability. | `POST /api/auth/password-reset/request/`, `POST /api/auth/password-reset/confirm/` | Backend OTP endpoints exist; web/mobile password reset UI coverage is documented as partial/limited. |
| JWT refresh if implemented | Not Implemented | Search URL config for token refresh route and test refresh call. | `backend/apps/users/urls.py`, `backend/config/urls.py` | Login returns refresh tokens, but no `/api/auth/token/refresh/` route was identified. |

## 4. Organization and Access Control

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| HR head organization setup | Complete | Log in as HR head and create/view organization. | `POST /api/org/create/`, `GET /api/org/` | HR-head-only permission applies. |
| Recruiter/interviewer organization membership | Complete | Create members or use seeded members. | `GET/POST /api/org/members/`, `POST /api/org/members/bulk/` | Membership records drive role-specific organization access. |
| Organization isolation | Complete | Attempt to access another organization's jobs/applications/analytics. | Backend organization filters in apps; `FINAL_SYSTEM_GAP_REPORT.md` | Major flows filter by active membership; production hardening/audit remains a future enhancement. |
| Users cannot access data from another organization | Manual Verification Required | Run negative manual/API tests with two organizations and users. | `TESTING_GUIDE.md`, API endpoints across jobs/applications/interviews/hiring | Code supports isolation, but final demo should include at least one negative test rehearsal. |
| Demo HR-head bootstrap or seed command exists | Complete | Run either bootstrap or full demo seed. | `python manage.py bootstrap_demo_hr_head`, `python manage.py seed_demo_data` | Full seed is recommended for the final demo. |

## 5. Job Posting Workflow

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Recruiter can create job posting | Complete | Log in as recruiter and create a job. | `POST /api/jobs/`, React recruiter jobs page | Subscription open-job limits may apply. |
| Recruiter can update job posting | Complete | Edit an existing job. | `PATCH /api/jobs/<job_id>/` | Recruiter must own the job in own organization. |
| Recruiter can manage job requirements | Complete | Add/update requirement records. | `POST/PUT /api/jobs/<job_id>/requirements/` | Requirements support screening/ranking. |
| Recruiter can manage evaluation criteria | Complete | Configure interview evaluation form. | `POST/PUT /api/jobs/<job_id>/eval-form/` | Used by interview evaluation flow. |
| Applicant can view open jobs | Complete | Log in as applicant and list open jobs. | `GET /api/jobs/`, Flutter jobs screen | Applicants should only see open/active jobs. |
| Applicant can save/apply for jobs | Complete | Save a job and submit application. | `POST /api/jobs/<job_id>/save/`, `POST /api/jobs/<job_id>/apply/` | Application requires applicant role and resume/application data. |

## 6. Job Application Workflow

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Applicant can submit application | Complete | Submit to an open job as applicant. | `POST /api/jobs/<job_id>/apply/`, Flutter application screen | Duplicate application validation should be rehearsed. |
| Resume/application data can be stored | Complete | Upload resume and inspect application/resume fields. | `POST /api/auth/resume/upload/`, application models | Local media storage is used for demo. |
| Recruiter can view applications | Complete | List applications as recruiter. | `GET /api/applications/`, React recruiter applications page | Scoped to recruiter's organization/jobs. |
| Recruiter can reject or shortlist where appropriate | Complete | Use shortlist/reject endpoints after screening/review. | `POST /api/applications/<id>/shortlist/`, `POST /api/applications/<id>/reject/` | Recruiter final decision-making remains manual. |
| Applicant can view application status | Complete | Log in as applicant and list applications/status history. | `GET /api/applications/`, `GET /api/applications/<id>/status-history/`, mobile status screen | Status updates should appear after workflow actions. |
| Application statuses follow correct lifecycle | Partial | Walk the full scripted lifecycle from apply to hired/rejected. | `backend/apps/applications/models.py`, `FINAL_DEMO_SCRIPT.md` | Current code supports final `hired` on offer acceptance; HR rejection applicant notification remains limited, and date/state edge cases still need manual checks. |

## 7. AI Resume Screening

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Resume text extraction from PDF/DOCX | Complete | Screen text-based PDF/DOCX resumes. | `backend/apps/ai_services/resume_text_extractor.py`, `POST /api/applications/<id>/screen/` | OCR for scanned/image-only resumes is not supported. |
| Resume preprocessing | Complete | Review service tests and run screening. | `backend/apps/ai_services/resume_preprocessor.py` | Normalizes text before scoring. |
| Skill extraction | Complete | Screen demo resume with known skills. | `backend/apps/ai_services/skill_extractor.py` | Skill dictionary coverage is finite; prepare demo data with expected keywords. |
| Education extraction | Complete | Screen resume with education content. | `backend/apps/ai_services/education_extractor.py` | Heuristic/prototype extraction. |
| Experience extraction | Complete | Screen resume with years/experience phrases. | `backend/apps/ai_services/experience_extractor.py` | Heuristic/prototype extraction. |
| Semantic matching | Complete | Run screening with and without Sentence-BERT dependency/model. | `backend/apps/ai_services/semantic_matcher.py` | Optional Sentence-BERT; fallback is lexical. |
| Safe fallback when Sentence-BERT/model is unavailable | Complete | Disable dependency/model and run screening. | `backend/apps/ai_services/semantic_matcher.py`, `AI_ALGORITHM_VALIDATION_REPORT.md` | Fallback prevents crash but is less semantically rich. |
| Hybrid formula is implemented | Complete | Run scoring tests or inspect scoring service. | `backend/apps/ai_services/scoring.py` | Formula: `0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score`. |
| Score explanation is stored | Complete | Screen application and inspect serialized fields/model. | `backend/apps/applications/models.py`, `backend/apps/ai_services/resume_screening.py` | Component scores and explanation metadata are persisted. |
| AI does not automatically make final hiring decisions | Complete | Screen low-score application and confirm it is rejected due to underqualification, while qualified candidates still require recruiter/HR review. | `POST /api/applications/<id>/screen/`, `ALGORITHMS.md` | Low score becomes `rejected`; qualified applicants remain available for recruiter actions such as assign interviewer or reject. |

## 8. Candidate Ranking

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Recruiter can view qualified candidate rankings | Complete | Call ranking endpoint as owning recruiter. | `GET /api/jobs/<job_id>/ranked-candidates/` | Role and organization scoped, and only `screened_qualified` applications are ranked. |
| Ranking uses `final_score` descending | Complete | Create multiple screened applications and compare order. | `backend/apps/applications/views.py` | Uses descending `final_score`, nulls last. |
| Equal score ordering is stable | Complete | Create equal-score applications and confirm earlier application first. | `backend/apps/applications/views.py` | Tie-breaker uses `applied_at`. |
| Candidate ranking page displays AI scores | Complete | Open recruiter ranking page after screening. | React recruiter ranking page | Display should be manually checked with seeded/screened data. |
| Candidate ranking does not replace recruiter decision-making | Complete | Verify shortlist/reject remains a recruiter action. | Ranking endpoint plus shortlist/reject endpoints | Ranking is advisory. |

## 9. Interview Management

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Recruiter can assign interviewer | Complete | Assign interviewer to a shortlisted/screened applicant. | `POST /api/applications/<id>/assign-interviewer/` or interview assignment route in API docs | Organization membership required. |
| Interviewer can view assigned interviews | Complete | Log in as interviewer and list assignments. | `GET /api/interviews/assigned/`, React interviewer page | Scoped to assigned interviewer. |
| Interviewer can send interview invitation | Complete | Send invitation for assigned interview. | `POST /api/interviews/<id>/send-invitation/` | Sends notification/email behavior in demo mode. |
| Applicant can accept/decline invitation | Complete | Respond through mobile app or API. | `POST /api/interview-invitations/<id>/accept/`, `POST /api/interview-invitations/<id>/decline/` | Applicant ownership enforced. |
| Invitation status updates correctly | Complete | Inspect invitation/interview status after accept/decline. | Invitation endpoints, mobile invitation detail screen | Status histories should be checked in demo data. |
| Past/duplicate invitation validation if implemented | Partial | Try sending past-date and duplicate active invitations. | `backend/apps/interviews/views.py` | Known limitations mention date/state validation still needs hardening. |

## 10. Interview Recording, Transcript, and AI Summary

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Interviewer can upload/select recording if implemented | Complete | Upload recording for assigned interview. | `POST /api/interviews/<id>/recordings/`, React interviewer transcript page | File type/size behavior should be manually checked with sample audio. |
| Transcript generation works in demo/mock mode | Complete | Upload recording and transcribe. | `POST /api/evaluations/recordings/<recording_id>/transcribe/` | Mock/default transcript is deterministic for demo reliability. |
| Optional real transcription is disabled unless configured | Complete | Check environment without API key and transcribe. | `backend/apps/ai_services/transcription_service.py`, `KNOWN_LIMITATIONS.md` | Real provider requires explicit OpenAI settings and is not needed for demo. |
| AI summary generation works in demo/mock mode | Complete | Generate summary from transcript. | `POST /api/evaluations/transcripts/<transcript_id>/generate-summary/` | Mock/default summary is generic but stable. |
| AI summary contains strengths | Complete | Inspect generated summary payload. | `backend/apps/ai_services/summary_service.py` | Required structured field. |
| AI summary contains weaknesses | Complete | Inspect generated summary payload. | `backend/apps/ai_services/summary_service.py` | Required structured field. |
| AI summary contains `communication_score` | Complete | Inspect generated summary payload. | `backend/apps/ai_services/summary_service.py` | Current persisted score uses a 0-10 style scale. |
| AI summary contains `overall_impression` | Complete | Inspect generated summary payload. | `backend/apps/ai_services/summary_service.py` | Required structured field. |
| AI summary contains `editable_summary_text` | Complete | Inspect generated summary payload. | `backend/apps/ai_services/summary_service.py` | Interviewer can revise this text. |
| Interviewer can edit summary | Complete | Patch summary fields. | `PATCH /api/evaluations/interview-summaries/<summary_id>/` | Assigned interviewer permission applies. |
| Interviewer can submit evaluation | Complete | Submit evaluation after interview. | `POST /api/interviews/<id>/evaluations/` | Application moves toward evaluation-submitted workflow. |

## 11. Hiring Decision and HR Approval

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Recruiter can only submit hiring decision after evaluation is complete | Complete | Try submitting before and after `evaluation_submitted`. | `POST /api/applications/<id>/hiring-decision/`, `backend/apps/hiring/views.py` | Backend gate requires evaluation-submitted status. |
| Recruiter can recommend hire/reject | Complete | Submit recommendation as recruiter. | `POST /api/applications/<id>/hiring-decision/` | Decision remains pending HR approval. |
| HR head can approve/reject hiring decision | Complete | Log in as HR head and review pending decision. | `POST /api/hiring-decisions/<id>/approve/`, `POST /api/hiring-decisions/<id>/reject/` | Organization-scoped. |
| Application status updates correctly | Complete | Inspect status and stage history after decisions. | `GET /api/applications/<id>/status-history/` | Hire approval moves to HR-approved; offer acceptance moves to hired. |
| HR rejection notification behavior is documented | Partial | Review docs and test HR rejection path. | `KNOWN_LIMITATIONS.md`, `backend/apps/hiring/views.py` | HR rejection notifies recruiter; applicant-facing HR rejection notification remains a limitation unless business meaning is clarified. |
| Hiring flow follows correct business order | Complete | Follow final demo script sequence. | `FINAL_DEMO_SCRIPT.md` | Backend now enforces evaluation-before-decision. |

## 12. Job Offer and Final Hiring Outcome

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Recruiter can send job offer after HR approval | Complete | Approve hire decision, then create offer. | `POST /api/applications/<id>/job-offer/` | Requires approved hire decision and `hr_approved` status. |
| Applicant can accept/reject offer | Complete | Respond through mobile app or API. | `POST /api/job-offers/<id>/accept/`, `POST /api/job-offers/<id>/decline/` | Applicant ownership enforced. |
| Accepted offer updates application lifecycle correctly | Complete | Accept offer and inspect application status/history. | `backend/apps/hiring/views.py`, `GET /api/applications/<id>/status-history/` | Acceptance marks the application `hired`. |
| Hired status is reflected in analytics if implemented | Complete | Accept an offer, then load analytics. | `GET /api/analytics/recruiter/`, `GET /api/analytics/hr-head/` | Analytics count `hired` applications. |
| Offer deadline validation if implemented | Complete | Try accepting after deadline. | `backend/apps/hiring/views.py` | Accept/decline endpoints check expired sent offers. Creation-time deadline constraints should still be manually checked. |

## 13. Notifications

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Application status notifications | Partial | Shortlist/reject/screen application and inspect applicant notifications. | `backend/apps/notifications/services.py`, `GET /api/notifications/` | Several key status changes notify users; HR rejection applicant notification remains limited. |
| Interview invitation notifications | Complete | Send invitation and inspect applicant notifications. | `POST /api/interviews/<id>/send-invitation/`, `GET /api/notifications/` | Application-level notification records, not push notifications. |
| Job offer notifications | Complete | Send offer and inspect applicant/relevant role notifications. | `POST /api/applications/<id>/job-offer/`, `GET /api/notifications/` | Console email may also show demo email. |
| Hiring decision notifications | Partial | Submit/approve/reject hiring decisions and inspect notifications. | Hiring decision endpoints, notifications API | HR decision notifications exist for recruiter; applicant coverage depends on approve/reject path. |
| Notification list/view endpoints or screens | Complete | List, mark read, read all, unread count. | `GET /api/notifications/`, `POST /api/notifications/read-all/`, React/mobile notification screens | Database-backed notifications only. |
| Mobile applicant notification visibility if implemented | Manual Verification Required | Run mobile app and inspect notification screen as applicant. | Flutter notifications screen | Requires Flutter device/emulator and seeded notification data. |

## 14. Analytics and PDF Reports

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Recruiter analytics | Complete | Log in as recruiter and call/load dashboard. | `GET /api/analytics/recruiter/`, React recruiter analytics page | Scoped to recruiter's organization/jobs. |
| Interviewer analytics | Complete | Log in as interviewer and call/load dashboard. | `GET /api/analytics/interviewer/`, React interviewer analytics page | Scoped to assigned/evaluated interviews. |
| HR head analytics | Complete | Log in as HR head and call/load dashboard. | `GET /api/analytics/hr-head/`, React HR-head analytics page | Organization-scoped. |
| PDF export endpoints | Complete | Call report endpoints and download/open PDF. | `GET /api/reports/recruiter-summary.pdf`, `GET /api/reports/interviewer-summary.pdf`, `GET /api/reports/hr-head-summary.pdf` | Requires `reportlab`. |
| `reportlab` dependency documented | Complete | Check backend requirements and docs. | `backend/requirements.txt`, `SETUP_GUIDE.md` | Required for PDF generation. |
| Analytics reflect hired/accepted outcomes correctly | Complete | Accept offer, verify `hired_count` and offer acceptance rate. | `backend/apps/analytics/services.py` | Depends on final lifecycle data. |
| Manual PDF export verification steps documented | Complete | Read testing/demo docs and perform export. | `TESTING_GUIDE.md`, `DEMO_GUIDE.md` | Manually confirm the PDF opens before demo. |

## 15. Billing and Subscription

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| HR head can view plans | Complete | Log in as HR head and list plans. | `GET /api/billing/plans/`, React billing page | Seed data creates demo plans. |
| Subscription creation works | Complete | Subscribe as HR head. | `POST /api/billing/subscribe/` | Organization membership required. |
| Demo payment flow works | Complete | Use demo payment success endpoint after subscription. | `POST /api/billing/demo-payment-success/` | No real charge; demo-only. |
| Real payment gateways remain optional | Complete | Leave Stripe keys blank and use demo flow. | `backend/apps/billing/payment_gateways.py`, `DEPLOYMENT_NOTES.md` | Optional Stripe code exists but is not required for FYP demo. |
| Stripe/PayPal/FPX keys are not required for demo mode | Complete | Run demo flow with no gateway credentials. | `.env` docs, demo billing endpoints | PayPal/FPX real integrations are not enabled by default. |
| Subscription limits are enforced if implemented | Complete | Try exceeding open-job limit after setting plan. | `backend/apps/billing/services.py`, job creation endpoint | Demo should explain current limit behavior. |
| Cancel/renew limitations are documented | Partial | Review known limitations/billing docs. | `KNOWN_LIMITATIONS.md`, `DEPLOYMENT_NOTES.md` | Full production billing lifecycle is not implemented; demo uses subscription/payment prototype flow. |

## 16. React Web Portal

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Web dependencies can be installed | Manual Verification Required | Run dependency install. | `cd web && npm ci` | Prior audit noted missing installed dependencies in workspace; final machine must install them. |
| Web app can run with `npm run dev` | Manual Verification Required | Start Vite dev server and open web portal. | `cd web && npm run dev` | Requires backend API URL and installed dependencies. |
| Web build can run with `npm run build` | Manual Verification Required | Build production bundle. | `cd web && npm run build` | Must be verified after `npm ci`. |
| HR head pages | Complete | Log in as HR head and visit organization, members, analytics, billing, approvals. | React HR-head routes/screens | Manual UI walkthrough recommended. |
| Recruiter pages | Complete | Log in as recruiter and visit jobs, applications, ranking, interviews, hiring, analytics. | React recruiter routes/screens | Some transcript/summary UX may require manual IDs/steps; rehearse the scripted path. |
| Interviewer pages | Complete | Log in as interviewer and visit assigned interviews, transcript/summary, evaluations, analytics. | React interviewer routes/screens | Verify with seeded/assigned interview. |
| Authentication flow | Complete | Log in/out as web roles. | React `/login`, auth service | Password reset UI is partial/not a primary demo path. |
| API base URL configuration documented | Complete | Check `.env.example` and web docs. | `web/.env.example`, `web/README.md` | Use LAN IP for device/browser if not localhost. |
| Known frontend limitations documented | Complete | Review known limitations and final gap report. | `KNOWN_LIMITATIONS.md`, `FINAL_SYSTEM_GAP_REPORT.md` | Explain prototype-level frontend gaps honestly if asked. |

## 17. Flutter Applicant Mobile App

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Flutter dependencies can be installed | Manual Verification Required | Run dependency install. | `cd mobile && flutter pub get` | Requires Flutter SDK. |
| `flutter analyze` can run | Manual Verification Required | Run analyzer. | `cd mobile && flutter analyze` | Prior audit environment did not have Flutter/Dart installed. |
| Applicant login | Complete | Run app and log in as demo applicant. | Flutter login screen, `POST /api/auth/login/` | Requires correct API base URL for emulator/device. |
| Job browsing | Complete | Browse open jobs in mobile app. | Flutter jobs screen, `GET /api/jobs/` | Requires seeded/open jobs. |
| Application submission/status | Complete | Submit application and inspect status/history. | Flutter applications/status screens | Resume upload/file picker behavior should be rehearsed on the chosen device. |
| Interview invitation response | Complete | Open invitation and accept/decline. | Flutter invitation screens, invitation endpoints | Requires pending invitation in seeded/demo state. |
| Job offer response | Complete | Open offer and accept/decline. | Flutter offers screen, job offer endpoints | Requires HR-approved offer sent first. |
| API base URL configuration documented | Complete | Review mobile README/setup instructions and app settings. | `mobile/README.md`, `mobile/lib/api/api_client.dart` | Use emulator host IP or LAN IP, not always `localhost`. |
| Known mobile limitations documented | Complete | Review known limitations and final gap report. | `KNOWN_LIMITATIONS.md`, `FINAL_SYSTEM_GAP_REPORT.md` | Mobile toolchain/build must be verified outside this workspace if Flutter is unavailable. |

## 18. Security and Permissions

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Default API permission requires authentication | Complete | Inspect DRF settings and call protected endpoint without token. | `backend/config/settings.py` | Default permission is `IsAuthenticated`. |
| Public endpoints are limited | Complete | Review views with `AllowAny`. | Register, login, password reset, Stripe webhook | Stripe webhook is public by design; validate signature behavior if using Stripe. |
| Role-based access is enforced | Complete | Run negative API checks across roles. | App views, `backend/apps/users/permissions.py` | Major role checks exist. |
| Organization-level access is enforced | Complete | Attempt cross-organization access. | Organization-scoped querysets/views | Production penetration testing remains future work. |
| Sensitive AI/payment/email/calendar keys are read from environment variables | Complete | Inspect settings/services. | `backend/config/settings.py`, AI/billing/email/calendar services | Do not commit real credentials. |
| Demo credentials are clearly marked as demo only | Complete | Review demo script/setup docs. | `FINAL_DEMO_SCRIPT.md`, `DEMO_GUIDE.md` | Seeded data uses fake/demo users. |
| OTP throttling/JWT refresh limitations are documented if not fully implemented | Partial | Review known limitations and API routes. | `KNOWN_LIMITATIONS.md`, auth URLs | Password reset OTP exists, but production throttling and JWT refresh endpoint/client handling are not complete. |

## 19. Optional Integrations

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| SendGrid/email integration status | Partial | Review email service/settings and send demo email. | `backend/apps/notifications/email_service.py`, `backend/config/settings.py` | Console email backend is default; SendGrid production delivery is optional/future. |
| Google Calendar integration status | Partial | Review calendar service behavior. | `backend/apps/interviews/calendar_service.py`, `KNOWN_LIMITATIONS.md` | Calendar integration is optional/not enabled as a real OAuth integration by default. |
| Stripe/PayPal/FPX integration status | Partial | Review billing gateways and demo payment path. | `backend/apps/billing/payment_gateways.py`, `DEPLOYMENT_NOTES.md` | Stripe optional code exists; PayPal/FPX real gateways are not default demo requirements. |
| OpenAI/Whisper/LLM integration status | Partial | Run transcription/summary without API key and with mocks. | `backend/apps/ai_services/transcription_service.py`, `backend/apps/ai_services/summary_service.py` | Real OpenAI calls are disabled unless explicitly configured. |
| Mock/fallback behavior documented | Complete | Review algorithm/limitations docs and run fallback tests. | `ALGORITHMS.md`, `AI_ALGORITHM_VALIDATION_REPORT.md`, `KNOWN_LIMITATIONS.md` | Mock/fallback behavior is required for demo stability. |
| External APIs are not required for core FYP demo | Complete | Run demo with blank external keys. | `FINAL_DEMO_SCRIPT.md`, `DEMO_GUIDE.md` | Core demo should not depend on paid/real services. |

## 20. Demo Data and Demo Script

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| `seed_demo_data` command exists | Complete | Run seed command. | `cd backend && python manage.py seed_demo_data` | Idempotent and updates known demo records. |
| Demo users exist | Complete | Run seed command and log in with each demo email. | `FINAL_DEMO_SCRIPT.md` | Password defaults to `DemoPass123!` unless overridden. |
| Demo organization exists | Complete | Run seed command and view organization. | `TechNova Solutions Sdn Bhd` seeded by command | Fake demo organization. |
| Demo job/application/interview/hiring data exists | Complete | Run seed command and inspect dashboards. | `python manage.py seed_demo_data` | Data is fake and designed for presentation. |
| `FINAL_DEMO_SCRIPT.md` exists | Complete | Open script and rehearse sequence. | `FINAL_DEMO_SCRIPT.md` | Presenter runbook for final demo. |
| `DEMO_GUIDE.md` exists | Complete | Open guide and follow setup/workflow. | `DEMO_GUIDE.md` | Includes demo mode guidance. |
| Backup plan exists | Complete | Review troubleshooting section. | `FINAL_DEMO_SCRIPT.md`, `DEMO_GUIDE.md` | Includes fallback explanations for AI/payment/tooling issues. |
| Demo credentials are documented | Complete | Review setup/demo script after seed command. | `FINAL_DEMO_SCRIPT.md`, `SETUP_GUIDE.md` | Demo-only credentials must not be reused in production. |

## 21. Testing Readiness

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| Backend test command documented | Complete | Read testing guide. | `TESTING_GUIDE.md`, `python manage.py test` | Requires PostgreSQL. |
| React build/lint command documented | Complete | Read setup/testing docs. | `npm run lint`, `npm run build` | Requires `npm ci` first. |
| Flutter analyze command documented | Complete | Read setup/testing docs. | `flutter analyze` | Requires Flutter SDK. |
| Manual smoke test checklist exists | Complete | Follow demo/testing guide. | `TESTING_GUIDE.md`, `DEMO_GUIDE.md`, `FINAL_DEMO_SCRIPT.md` | Use this checklist as the final smoke checklist. |
| External services are mocked/disabled in tests | Complete | Review AI validation and tests. | `AI_ALGORITHM_VALIDATION_REPORT.md`, backend tests | Tests should not call real external APIs. |
| PostgreSQL test requirement is documented | Complete | Review setup/testing docs and settings. | `backend/config/settings.py`, `TESTING_GUIDE.md` | Start PostgreSQL before tests. |

## 22. Documentation Readiness

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| `README.md` complete | Complete | Read project overview and setup links. | `README.md` | This checklist adds final readiness detail. |
| `SETUP_GUIDE.md` complete | Complete | Follow local setup steps. | `SETUP_GUIDE.md` | Validate commands on final machine. |
| `API_DOCUMENTATION.md` complete | Complete | Compare API docs with routes during smoke testing. | `API_DOCUMENTATION.md` | Update later if endpoints change. |
| `TESTING_GUIDE.md` complete | Complete | Follow testing commands/checklist. | `TESTING_GUIDE.md` | Environment still required. |
| `DEMO_GUIDE.md` complete | Complete | Use for demo setup and presentation. | `DEMO_GUIDE.md` | Pair with final demo script. |
| `DEPLOYMENT_NOTES.md` complete | Complete | Review deployment environment and limitations. | `DEPLOYMENT_NOTES.md` | Local/demo deployment is recommended for FYP. |
| `KNOWN_LIMITATIONS.md` complete | Complete | Review before submission and examiner questions. | `KNOWN_LIMITATIONS.md` | Honest prototype limitations are documented. |
| `FINAL_DEMO_SCRIPT.md` complete | Complete | Rehearse all steps. | `FINAL_DEMO_SCRIPT.md` | Use as presenter runbook. |
| `AI_ALGORITHM_VALIDATION_REPORT.md` complete | Complete | Review algorithm validation evidence. | `AI_ALGORITHM_VALIDATION_REPORT.md` | Documents tests, fallbacks, and AI limitations. |

## 23. Report Alignment

| Checklist item | Status | How to verify | Related file, endpoint, command, or screen | Notes / limitations |
|---|---|---|---|---|
| System matches FYP written requirements | Partial | Compare FYP summary with completed flows and known limitations. | `FYP_REQUIREMENTS_SUMMARY.md`, `FINAL_SYSTEM_GAP_REPORT.md`, this checklist | Core workflows are substantially covered, but optional integrations/production hardening remain limitations. |
| Algorithm implementation aligns with `ALGORITHMS.md` | Complete | Review AI services and validation report. | `ALGORITHMS.md`, `AI_ALGORITHM_VALIDATION_REPORT.md` | Mock/fallback behavior is preserved. |
| Chapter 4 incorrect diagrams are not treated as source of truth | Complete | Confirm team follows repository markdown source-of-truth rule. | `AGENTS.md` | Use corrected markdown/docs first. |
| UI screens can be used as reference | Complete | Use Chapter 4 UI only as visual reference if needed. | `AGENTS.md` | Do not derive backend data model/process from incorrect diagrams. |
| Known limitations and future enhancements are documented honestly | Complete | Review limitations docs before submission. | `KNOWN_LIMITATIONS.md`, `FINAL_SYSTEM_GAP_REPORT.md` | Present as academic prototype limitations, not hidden defects. |

---

## 24. Final Demo Readiness Summary

| Area | Status | Demo Risk | Required action before demo |
|---|---|---|---|
| Project setup/documentation | Complete | Low | Rehearse setup commands once on final machine. |
| Backend foundation | Manual Verification Required | Medium | Confirm PostgreSQL is running, migrations pass, `python manage.py check` passes, and seed data loads. |
| Authentication/roles | Partial | Medium | Use seeded users; avoid password reset/JWT refresh as main demo path unless backend-only endpoints are shown. |
| Organization/access control | Complete | Low | Rehearse one negative access-control example if time allows. |
| Job posting | Complete | Low | Prepare recruiter demo job and requirements. |
| Application workflow | Partial | Medium | Rehearse exact lifecycle and status transitions with seed data. |
| AI resume screening | Complete | Low | Use text-based PDF/DOCX resumes; explain no OCR and possible lexical fallback. |
| Candidate ranking | Complete | Low | Pre-screen candidates so ranking page has visible scores. |
| Interview management | Partial | Medium | Rehearse invitation timing/duplicate cases; avoid invalid date edge cases in live demo. |
| Transcript and AI summary | Complete | Low | Present mock/demo mode clearly and show editability. |
| Hiring decision/HR approval | Complete | Low | Follow order: evaluation submitted -> recruiter decision -> HR approval/rejection. |
| Job offer/final outcome | Complete | Low | Accept offer in mobile and verify `hired` appears in analytics. |
| Notifications | Partial | Medium | Demonstrate invitation/offer/application notifications; explain HR rejection applicant-notification limitation if asked. |
| Analytics/PDF reports | Complete | Medium | Confirm reportlab installed and PDFs open on demo machine. |
| Billing/subscription | Partial | Medium | Demonstrate demo payment only; do not rely on real gateways. |
| React web portal | Manual Verification Required | Medium | Run `npm ci`, `npm run build`, and full browser smoke test. |
| Flutter applicant app | Manual Verification Required | High | Run `flutter pub get`, `flutter analyze`, and a device/emulator smoke test before demo. |
| Security/permissions | Partial | Medium | Explain demo/prototype limitations: no production throttling/MFA, limited JWT refresh support. |
| Optional integrations | Partial | Low | State clearly that external APIs are optional and not required for demo. |
| Demo data/script | Complete | Low | Run `seed_demo_data` immediately before final rehearsal. |
| Testing readiness | Manual Verification Required | Medium | Run backend tests with PostgreSQL; verify web/mobile checks where toolchains exist. |
| Documentation readiness | Complete | Low | Include this checklist in submission package. |
| Report alignment | Partial | Medium | Ensure final report explains implemented prototype scope and limitations honestly. |

---

## 25. Final Action List

### Must fix before demo

1. Verify PostgreSQL is installed/running and backend commands pass: `python manage.py check`, `python manage.py migrate`, `python manage.py seed_demo_data`.
2. Run the complete final demo script once without interruption using only demo data.
3. Verify the React web portal starts and builds after `npm ci`.
4. Verify the Flutter app runs on the actual demo emulator/device and can reach the backend API base URL.
5. Pre-screen demo applications so candidate ranking and AI score fields are visible.
6. Generate/open each PDF report once on the final machine.
7. Confirm accepted job offer transitions to `hired` and updates analytics in the demo database.

### Should fix before submission

1. Add or verify applicant-facing notification behavior for HR-rejected hiring decisions, or clearly document the intended business meaning of HR rejection as internal rework.
2. Add/verify client-side password reset screens if password reset is expected in the examiner demo.
3. Add/verify JWT refresh endpoint/client refresh behavior if long sessions are expected.
4. Harden interview invitation duplicate/date validation and document exact behavior.
5. Confirm job-offer creation deadline validation behavior and add any missing negative tests.
6. Re-run backend business-flow tests with PostgreSQL and record results for submission evidence.

### Nice to have

1. Improve recruiter UI labels for AI mock/fallback mode and score explanations.
2. Package/cached Sentence-BERT model for an offline demo environment if semantic quality is important.
3. Add screenshots to demo documentation after final UI rehearsal.
4. Add a small two-organization negative-permission demo scenario.
5. Improve mobile/web automated test coverage.

### Can explain as limitation/future enhancement

1. OCR for scanned resumes is not supported.
2. Real OpenAI/Whisper/LLM calls are optional and disabled unless configured.
3. Real SendGrid email, Google Calendar OAuth, Stripe/PayPal/FPX payment gateways, and mobile push notifications are not required for the core FYP demo.
4. Local media storage and console email are demo/prototype choices.
5. Production hardening items such as MFA, account lockout, advanced throttling, full audit logging, CI/CD, cloud storage, backups, monitoring, and penetration testing are future enhancements.
6. Billing cancel/renew flows and full production subscription lifecycle remain prototype/future work unless explicitly added later.
