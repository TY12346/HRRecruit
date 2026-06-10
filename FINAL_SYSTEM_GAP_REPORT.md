# FINAL SYSTEM GAP REPORT

## Audit scope

This regression audit reviewed the repository against `AGENTS.md`, `FYP_REQUIREMENTS_SUMMARY.md`, `ALGORITHMS.md`, `AI_ALGORITHM_VALIDATION_REPORT.md`, and the current backend, React web portal, and Flutter mobile app implementation.

Areas checked:

1. Backend APIs
2. React web portal
3. Flutter mobile app
4. Authentication and role permissions
5. Organization isolation
6. Job posting workflow
7. Application workflow
8. AI resume screening
9. Candidate ranking
10. Interview invitation flow
11. Interview evaluation, transcript, and summary
12. Hiring decision and HR approval
13. Notifications
14. Analytics and PDF export
15. Billing and payment flow
16. Optional integrations if implemented

## Executive summary

The system has substantial coverage for the FYP demo: Django REST APIs are role protected by default, organization membership checks are present in the major recruiter/interviewer/HR-head flows, AI resume screening follows the required weighted formula, candidate ranking is implemented, interview transcript/summary features use deterministic mock-first services, notifications exist, analytics and PDF report endpoints exist, and both the React web portal and Flutter applicant app have route/API coverage for many workflows.

However, several gaps can block or weaken a final FYP demonstration:

- The hiring decision API and React hiring screen allow recruiters to submit a hire/reject recommendation for applications that have not completed the interview/evaluation stage.
- Accepting a job offer does not transition the application to `hired`, so the end-to-end hiring lifecycle and hire analytics remain incomplete.
- There is no web/mobile password reset UI even though backend OTP reset endpoints exist.
- HR-head account bootstrap is not exposed as a normal product flow; the demo needs an admin/superuser/manual seed step.
- Several date/state validations are missing around invitations and job offers.
- Optional Stripe sandbox code is present, which should remain disabled for early FYP demo unless explicitly justified.

## Regression findings

### GAP-001: Recruiters can submit hiring decisions before interview evaluation is complete

- **Issue description:** `HiringDecisionSubmitAPIView` blocks only terminal statuses such as withdrawn/rejected/offered/hired, but it does not require `EVALUATION_SUBMITTED` or another post-interview status before allowing a recruiter to submit a hire/reject recommendation. The React hiring decision page also loads all applications and does not filter to evaluated candidates.
- **Affected files:**
  - `backend/apps/hiring/views.py`
  - `web/src/pages/recruiter/HiringDecisionPage.jsx`
  - `backend/apps/evaluations/serializers.py`
  - `backend/apps/applications/models.py`
- **Affected user role:** Recruiter, HR Head, Applicant
- **Severity:** High
- **Recommended fix:** Require `application.status == evaluation_submitted` or an explicitly allowed post-evaluation state before creating a hiring decision. Update the React page to show only eligible evaluated candidates and add backend tests proving submitted/screened/shortlisted/interview-invited applications cannot be sent to HR.
- **Blocks FYP demo:** Yes, if demonstrating the full interview-to-hiring decision workflow in the required order.

### GAP-002: Accepted offers never become `hired`

- **Issue description:** `JobOfferAcceptAPIView` changes the application status to `offer_accepted`, but never transitions to the existing `hired` status. Analytics counts hires using `JobApplication.Status.HIRED`, so successful hires remain invisible in hire counts and final funnel metrics.
- **Affected files:**
  - `backend/apps/hiring/views.py`
  - `backend/apps/applications/models.py`
  - `backend/apps/analytics/services.py`
  - `mobile/lib/services/applicant_workflow_service.dart`
  - `web/src/pages/hr_head/HRAnalyticsPage.jsx`
  - `web/src/pages/recruiter/RecruiterAnalyticsPage.jsx`
- **Affected user role:** Applicant, Recruiter, HR Head
- **Severity:** High
- **Recommended fix:** Decide whether accepting an offer should immediately set `hired` or whether a recruiter/HR confirmation endpoint is needed. For the FYP demo, the simplest fix is to set `HIRED` after `ACCEPTED` and keep `offer_status=accepted`, or add a recruiter confirmation endpoint and update analytics to count both accepted offers and hired applications consistently.
- **Blocks FYP demo:** Yes, if the demo includes final hiring outcome or analytics hire counts.

### GAP-003: HR rejection of a pending hiring decision does not notify the applicant

- **Issue description:** When HR rejects a pending hiring decision, the application changes to `hr_rejected` and the recruiter is notified, but the applicant is not notified. The requirements state applicants should receive rejection/status updates.
- **Affected files:**
  - `backend/apps/hiring/views.py`
  - `backend/apps/notifications/services.py`
  - `mobile/lib/services/applicant_workflow_service.dart`
- **Affected user role:** Applicant, HR Head, Recruiter
- **Severity:** Medium
- **Recommended fix:** Add an applicant notification when HR rejection is intended to be a final applicant-facing rejection. If HR rejection only means “rework recruiter decision,” introduce a clearer internal status and do not expose it as a final applicant rejection.
- **Blocks FYP demo:** Partial. It blocks a clean applicant rejection-notification demo for HR-rejected decisions.

### GAP-004: Hiring-decision UI does not guide recruiters toward evaluated candidates

- **Issue description:** The React hiring decision page lists recent applications from all statuses and provides a submit button without frontend eligibility checks. This amplifies GAP-001 and makes it easy during a demo to submit a decision too early.
- **Affected files:**
  - `web/src/pages/recruiter/HiringDecisionPage.jsx`
  - `web/src/api/client.js`
- **Affected user role:** Recruiter
- **Severity:** High
- **Recommended fix:** Filter candidates to `evaluation_submitted` or backend-provided eligible candidates, disable submit when selected status is not eligible, and display the interview evaluation/AI summary as supporting evidence.
- **Blocks FYP demo:** Yes, because it can make the demonstrated workflow look out of sequence.

### GAP-005: Interview invitations can be sent for past dates and multiple pending invitations can coexist

- **Issue description:** `SendInterviewInvitationSerializer` validates meeting link/location by mode, but does not require `proposed_datetime` to be in the future. The send endpoint also creates a new invitation without expiring/cancelling prior pending invitations for the same interview.
- **Affected files:**
  - `backend/apps/interviews/serializers.py`
  - `backend/apps/interviews/views.py`
  - `mobile/lib/services/applicant_workflow_service.dart`
  - `web/src/pages/interviewer/SendInvitationPage.jsx`
- **Affected user role:** Interviewer, Applicant
- **Severity:** Medium
- **Recommended fix:** Validate future `proposed_datetime`, prevent duplicate pending invitations or automatically mark old pending invitations as expired/replaced, and add tests for old-link acceptance.
- **Blocks FYP demo:** No, if demo data is controlled; yes if accidental past or duplicate invitations are created live.

### GAP-006: Job offers can be created with past response deadlines

- **Issue description:** `JobOfferCreateSerializer` validates message and optional offer-letter file, but does not reject `respond_deadline` values in the past.
- **Affected files:**
  - `backend/apps/hiring/serializers.py`
  - `backend/apps/hiring/views.py`
  - `web/src/pages/recruiter/JobOfferPage.jsx`
  - `mobile/lib/services/applicant_workflow_service.dart`
- **Affected user role:** Recruiter, Applicant
- **Severity:** Medium
- **Recommended fix:** Add serializer validation requiring a future response deadline. Add frontend min date/time constraints and backend tests.
- **Blocks FYP demo:** No, if demo data is controlled.

### GAP-007: Password reset APIs exist, but web and mobile UI flows are missing

- **Issue description:** Backend password reset request/confirm endpoints exist, but there are no React or Flutter screens/services wired to those endpoints. Users cannot complete reset password from either client without manually calling the API.
- **Affected files:**
  - `backend/apps/users/views.py`
  - `backend/apps/users/urls.py`
  - `backend/apps/users/serializers.py`
  - `web/src/pages/auth/LoginPage.jsx`
  - `web/src/api/client.js`
  - `mobile/lib/services/applicant_auth_service.dart`
  - `mobile/lib/router/app_router.dart`
- **Affected user role:** Applicant, Recruiter, Interviewer, HR Head
- **Severity:** Medium
- **Recommended fix:** Add web and mobile forgot-password/request-OTP/confirm-reset screens, API client functions, form validation, and success/error handling.
- **Blocks FYP demo:** Partial. It blocks demoing password reset as a user-facing requirement.

### GAP-008: OTP reset lacks attempt limiting and resend throttling

- **Issue description:** The OTP reset flow stores six-digit OTPs with expiry, but does not limit request frequency, OTP verification attempts, or invalidate older OTPs when a new one is issued.
- **Affected files:**
  - `backend/apps/users/models.py`
  - `backend/apps/users/serializers.py`
  - `backend/apps/users/views.py`
- **Affected user role:** Applicant, Recruiter, Interviewer, HR Head
- **Severity:** Medium
- **Recommended fix:** Add attempt counters, per-user/IP throttling, resend cooldown, and invalidate previous unused OTPs after successful reset or new issuance.
- **Blocks FYP demo:** No, but it is a security gap.

### GAP-009: Web and mobile clients do not refresh expired JWT access tokens automatically

- **Issue description:** The backend uses SimpleJWT refresh tokens, and logout blacklists refresh tokens, but the React Axios client and Flutter Dio client only attach the current access token. Neither client calls a refresh endpoint on 401, and the backend does not expose SimpleJWT refresh routes.
- **Affected files:**
  - `backend/config/urls.py`
  - `backend/config/settings.py`
  - `web/src/api/client.js`
  - `web/src/store/authStore.js`
  - `mobile/lib/api/api_client.dart`
  - `mobile/lib/services/token_storage.dart`
- **Affected user role:** Applicant, Recruiter, Interviewer, HR Head
- **Severity:** Medium
- **Recommended fix:** Expose `TokenRefreshView`, add client-side 401 refresh/retry logic, and clear auth state only when refresh fails.
- **Blocks FYP demo:** Possible, if the demo session exceeds the access token lifetime or stale tokens are reused.

### GAP-010: HR-head account bootstrap is not exposed as a normal product flow

- **Issue description:** Applicant self-registration exists and HR heads can create organizations after logging in, but there is no public HR-head registration/onboarding endpoint or web flow. A demo must rely on admin-created users, superuser creation, fixtures, or manual database setup.
- **Affected files:**
  - `backend/apps/users/views.py`
  - `backend/apps/users/serializers.py`
  - `backend/apps/organizations/views.py`
  - `web/src/pages/auth/LoginPage.jsx`
  - `web/src/routes/router.jsx`
- **Affected user role:** HR Head
- **Severity:** High
- **Recommended fix:** Add a documented seed command for demo HR-head accounts or an explicit HR-head invitation/onboarding flow. For FYP, a management command plus README demo credentials may be enough.
- **Blocks FYP demo:** Yes, unless the demo environment is pre-seeded.

### GAP-011: Candidate profile UI renders structured extraction objects poorly

- **Issue description:** The interviewer candidate detail page prints `resume.extracted_experience` and `resume.extracted_education` directly. These values are JSON objects from the backend, so they may display as `[object Object]` instead of readable years/roles/degree/field details.
- **Affected files:**
  - `web/src/pages/interviewer/CandidateDetailPage.jsx`
  - `backend/apps/applications/serializers.py`
- **Affected user role:** Interviewer
- **Severity:** Low
- **Recommended fix:** Format extracted experience and education fields into human-readable summaries, matching the recruiter candidate profile UI.
- **Blocks FYP demo:** No, but it weakens the AI extraction presentation.

### GAP-012: Transcript and summary page depends on manually entered recording/transcript IDs

- **Issue description:** The interviewer transcript/summary page requires the user to manually enter or rely on locally stored recording/transcript IDs instead of discovering recordings/transcripts for the current interview. This can break demo flow after refresh or when switching browsers.
- **Affected files:**
  - `web/src/pages/interviewer/TranscriptSummaryPage.jsx`
  - `web/src/api/client.js`
  - `backend/apps/evaluations/views.py`
- **Affected user role:** Interviewer
- **Severity:** Medium
- **Recommended fix:** Add endpoints or serializer fields to list recordings/transcripts/summaries for an interview and update the UI to select the latest available item automatically.
- **Blocks FYP demo:** Partial. It can interrupt the interview transcription/summary demo.

### GAP-013: Optional Stripe sandbox integration is present despite mock/demo payment being the stated early-development path

- **Issue description:** The codebase includes Stripe settings, checkout-session creation, and a public Stripe webhook endpoint. The repository instructions say not to use real payment integrations unless explicitly requested and to use a demo payment flow for early development. Although tests mock the provider, this increases configuration/demo risk and should be clearly disabled or documented as optional.
- **Affected files:**
  - `backend/config/settings.py`
  - `backend/apps/billing/models.py`
  - `backend/apps/billing/views.py`
  - `backend/apps/billing/payment_gateways.py`
  - `backend/apps/billing/serializers.py`
  - `backend/apps/billing/urls.py`
- **Affected user role:** HR Head
- **Severity:** Medium
- **Recommended fix:** Keep demo gateway as the default and hide Stripe/PayPal/FPX options from the UI unless an explicit environment flag enables optional gateways. Document that no real payments are required for the FYP demo.
- **Blocks FYP demo:** No, if demo payment flow is used.

### GAP-014: Billing has no cancel/renew management endpoint

- **Issue description:** Subscriptions can be created, upgraded, activated through demo payment, and listed, but there is no endpoint for cancelling auto-renew, cancelling a subscription, or manually renewing an expiring subscription beyond creating another pending subscription.
- **Affected files:**
  - `backend/apps/billing/views.py`
  - `backend/apps/billing/services.py`
  - `backend/apps/billing/urls.py`
  - `web/src/pages/hr_head/BillingPage.jsx`
- **Affected user role:** HR Head
- **Severity:** Low
- **Recommended fix:** Add explicit cancel/renew endpoints or document that subscription renewal/cancellation is out of scope for the FYP demo.
- **Blocks FYP demo:** No, if only plan selection/demo payment is shown.

### GAP-015: Analytics/PDF export depends on runtime PDF dependency and was not verified in this environment

- **Issue description:** PDF report endpoints exist and the React clients call them, but this audit could not complete backend tests due unavailable PostgreSQL service. If `reportlab` or database setup is missing in the final demo environment, PDF export will fail.
- **Affected files:**
  - `backend/apps/analytics/views.py`
  - `backend/apps/analytics/reports.py`
  - `backend/requirements.txt`
  - `web/src/pages/recruiter/RecruiterAnalyticsPage.jsx`
  - `web/src/pages/interviewer/InterviewerAnalyticsPage.jsx`
  - `web/src/pages/hr_head/HRAnalyticsPage.jsx`
- **Affected user role:** Recruiter, Interviewer, HR Head
- **Severity:** Medium
- **Recommended fix:** Verify `reportlab` is installed in the final backend environment, add a smoke test for each PDF endpoint, and include PDF export in demo dry runs.
- **Blocks FYP demo:** Possible, if PDF export is demonstrated.

### GAP-016: AI resume screening has known OCR and semantic fallback limitations

- **Issue description:** AI screening follows the required formula and fallback behavior, but scanned-image resumes are not supported and the lexical semantic fallback is weaker than a real semantic model unless optional dependencies are installed/cached.
- **Affected files:**
  - `backend/apps/ai_services/resume_text_extractor.py`
  - `backend/apps/ai_services/semantic_matcher.py`
  - `backend/apps/ai_services/resume_screening.py`
  - `AI_ALGORITHM_VALIDATION_REPORT.md`
- **Affected user role:** Recruiter, Applicant
- **Severity:** Medium
- **Recommended fix:** Use text-based PDF/DOCX demo resumes, prepare demo job requirements/resumes with overlapping skills, and optionally add documented OCR or local model support later without removing fallback behavior.
- **Blocks FYP demo:** No, if demo resumes are controlled text-based files.

### GAP-017: Interview transcript/summary uses intentionally generic mock outputs

- **Issue description:** Mock-first transcript and AI summary behavior is correct for safe FYP development, but the generated transcript/summary may not reflect the actual uploaded audio or interview content. This can look unrealistic if not explained during the demo.
- **Affected files:**
  - `backend/apps/ai_services/transcription_service.py`
  - `backend/apps/ai_services/summary_service.py`
  - `web/src/pages/interviewer/TranscriptSummaryPage.jsx`
- **Affected user role:** Interviewer, Recruiter
- **Severity:** Low
- **Recommended fix:** Keep the mock fallback, but label outputs clearly as mock AI for demo mode or prepare a deterministic demo script that matches the mock output.
- **Blocks FYP demo:** No, but it should be verbally explained.

### GAP-018: Frontend build/lint dependencies are not installed in the current workspace

- **Issue description:** `npm run build` failed because `vite` was not available, and `npm run lint` failed because `@eslint/js` was not available. This appears to be an environment/dependency-installation issue rather than a source-code failure, but it prevents frontend regression verification in this workspace.
- **Affected files:**
  - `web/package.json`
  - `web/package-lock.json`
  - `web/vite.config.js`
  - `web/eslint.config.js`
- **Affected user role:** Recruiter, Interviewer, HR Head
- **Severity:** Medium
- **Recommended fix:** Run `npm ci` before frontend checks in CI/demo setup, then rerun `npm run lint` and `npm run build`.
- **Blocks FYP demo:** Possible, if the web app is not built/served from an environment with installed dependencies.

### GAP-019: Flutter toolchain is not available in the current workspace

- **Issue description:** The repository contains a Flutter mobile app, but `flutter` and `dart` commands were not available in this environment, so mobile static analysis/build could not be verified.
- **Affected files:**
  - `mobile/pubspec.yaml`
  - `mobile/lib/main.dart`
  - `mobile/lib/router/app_router.dart`
  - `mobile/lib/services/applicant_workflow_service.dart`
- **Affected user role:** Applicant
- **Severity:** Medium
- **Recommended fix:** Verify the applicant app with `flutter pub get`, `flutter analyze`, and a debug build on the final demo machine/emulator.
- **Blocks FYP demo:** Possible, if the applicant mobile app is demonstrated from this environment.

### GAP-020: Backend regression tests require PostgreSQL but no local PostgreSQL service is running

- **Issue description:** The backend test command discovered 149 tests but failed before execution because PostgreSQL at `127.0.0.1:5432` refused connections. The project correctly uses PostgreSQL from the start, but the demo/CI environment must provide the database service.
- **Affected files:**
  - `backend/config/settings.py`
  - `backend/requirements.txt`
  - Backend test modules under `backend/apps/*/tests.py`
- **Affected user role:** All roles indirectly
- **Severity:** Medium
- **Recommended fix:** Start PostgreSQL with the expected environment variables, or provide a documented docker-compose/dev setup for running the test suite.
- **Blocks FYP demo:** Possible, if backend cannot connect to PostgreSQL in the demo environment.

## Positive coverage confirmed

- **Authentication:** JWT authentication is configured globally in DRF, with authenticated access as the default permission class. Public endpoints are limited to registration, login, and password reset.
- **Roles:** Role constants match the required values: `applicant`, `recruiter`, `interviewer`, and `hr_head`.
- **Organization isolation:** Major recruiter, interviewer, HR-head, billing, analytics, application, interview, and hiring flows filter by active organization membership.
- **Job posting:** Recruiters can create, update, duplicate, configure requirements, and configure evaluation forms for their organization jobs. Applicants can search/open/save/apply to open jobs.
- **Application workflow:** Applicants can apply/withdraw; recruiters can screen, rank, shortlist, assign interviewers, reject, and add remarks.
- **AI resume screening:** Screening logic remains in `ai_services`, uses the required formula, records component scores/explanations, and marks low scores as `screened_not_qualified` rather than auto-rejecting.
- **Candidate ranking:** Recruiter ranking sorts by final score descending with nulls last and earlier application as tie breaker.
- **Interview workflow:** Interviewer assignment, invitation send, applicant accept/decline, mock calendar placeholder, recording upload, transcript generation, AI summary generation/edit, and evaluation submission are implemented.
- **Hiring/approval:** Recruiter decision submission, HR approval/rejection, and post-approval job offer sending are implemented.
- **Notifications:** Database notifications are created for key workflow events and scoped to each recipient.
- **Analytics/PDF:** Role-specific dashboards and PDF endpoints exist for recruiter, interviewer, and HR head.
- **Billing:** Plans, subscription creation/upgrade, invoice listing, demo payment activation, and open-job subscription limit enforcement exist.

## Recommended fix order

1. **Fix hiring lifecycle gate:** Restrict hiring decisions to evaluated candidates only and update the React hiring decision UI.
2. **Fix final hire transition:** Decide and implement how accepted offers become `hired`, then update analytics/tests.
3. **Complete critical notifications:** Add applicant-facing updates for HR-final rejection paths and verify mobile notification display.
4. **Add demo setup path:** Provide HR-head seed/demo setup documentation or a management command.
5. **Harden date/state validation:** Future invitation dates, single active pending invitation, future offer deadlines.
6. **Add password reset UI:** Web and mobile reset request/confirm screens and API client methods.
7. **Add JWT refresh support:** Backend refresh route and client refresh/retry interceptors.
8. **Improve demo polish:** Format structured AI extraction in web UI and remove manual ID entry for transcript/summary flow.
9. **Clarify billing integrations:** Keep only demo gateway visible by default and document optional Stripe sandbox flags.
10. **Stabilize verification environment:** Ensure PostgreSQL, web dependencies, and Flutter toolchain are installed before final demo rehearsal.

## Verification commands run during audit

- `find .. -name AGENTS.md -print`
- `cat AGENTS.md`
- `cat FYP_REQUIREMENTS_SUMMARY.md`
- `cat ALGORITHMS.md`
- `cat AI_ALGORITHM_VALIDATION_REPORT.md`
- `find backend/apps web/src mobile/lib -type f | sort`
- `rg -n "^class |^def |permission_classes|@transaction|@api_view" backend/apps -g 'views.py' -g 'urls.py' -g 'models.py' -g 'serializers.py' -g 'services.py' -g 'reports.py' -g 'payment_gateways.py'`
- `python backend/manage.py check`
- `python backend/manage.py test backend/apps --verbosity=1`
- `npm run build`
- `npm run lint`
- `flutter --version`
- `dart --version`

