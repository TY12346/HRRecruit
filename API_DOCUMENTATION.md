# HRRecruit API Documentation

This document summarizes the major backend API areas for examiner/demo review. It is intentionally high level and only lists example endpoints that are visible in the current Django URL configuration.

## API Base URL

Local backend base URL:

```text
http://localhost:8000/api
```

Protected endpoints require JWT Bearer token authentication:

```http
Authorization: Bearer <access_token>
```

The backend uses role-based permissions and organization data isolation. Recruiters and HR heads are scoped to their own organization. Interviewers are scoped to assigned interviews/candidates. Applicants are scoped to their own profile, applications, invitations, offers, and notifications.

## Authentication and Account APIs

**Purpose:** Register/login users, manage profile, logout, password reset, and applicant resume upload.

**Main roles:**

- Public: register, login, password reset request/confirm.
- Authenticated users: logout and profile.
- Applicant: resume upload.

**Confirmed example endpoints:**

| Method | Endpoint | Notes |
| --- | --- | --- |
| `POST` | `/api/auth/register/` | Register account. |
| `POST` | `/api/auth/login/` | Returns JWT tokens and user data. |
| `POST` | `/api/auth/logout/` | Authenticated logout/token blacklist flow. |
| `GET/PATCH` | `/api/auth/profile/` | Authenticated profile view/update. |
| `POST` | `/api/auth/password-reset/request/` | Demo/local email reset request. |
| `POST` | `/api/auth/password-reset/confirm/` | Confirm password reset. |
| `POST` | `/api/auth/resume/upload/` | Applicant resume upload. |

**Permission notes:** Protected account endpoints require authentication. Resume upload is limited to applicants.

## Users/Profile

**Purpose:** Provide authenticated users with their own profile data and allow profile updates.

**Main roles:** Applicant, recruiter, interviewer, HR head.

**Confirmed example endpoint:**

- `/api/auth/profile/`

**Permission notes:** Users can only access their own authenticated profile through this endpoint.

## Organization APIs

**Purpose:** Allow an HR head to create/manage the organization and team members.

**Main roles:** HR head.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/org/create/` | Create organization. |
| `/api/org/` | Retrieve/update organization profile. |
| `/api/org/members/` | List/create organization members. |
| `/api/org/members/bulk/` | Bulk import members. |
| `/api/org/members/<member_id>/deactivate/` | Deactivate member. |

**Permission notes:** These endpoints are HR-head controlled and scoped to the HR head's organization.

## Jobs APIs

**Purpose:** Manage job postings, requirements, evaluation forms, saved jobs, applications, and candidate rankings.

**Main roles:**

- Recruiter: create/update jobs, requirements, evaluation forms, duplicate jobs, view ranked candidates.
- Applicant: browse jobs, save jobs, apply.
- HR head/interviewer: may view organization/assigned job-related data where allowed by the views.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/jobs/` | List/create jobs. |
| `/api/jobs/saved/` | Applicant saved jobs. |
| `/api/jobs/<job_id>/` | Job detail/update where permitted. |
| `/api/jobs/<job_id>/duplicate/` | Duplicate a job. |
| `/api/jobs/<job_id>/requirements/` | Job requirements. |
| `/api/jobs/<job_id>/eval-form/` | Evaluation form builder data. |
| `/api/jobs/<job_id>/save/` | Save/unsave a job. |
| `/api/jobs/<job_id>/apply/` | Applicant application submission. |
| `/api/jobs/<job_id>/ranked-candidates/` | Candidate ranking for a job. |

**Permission notes:** Organization-owned job data is isolated by active organization membership. Applicants only act on their own saved jobs and applications.

## Applications APIs

**Purpose:** Manage job applications, screening, shortlisting, rejection, remarks, candidate profiles, status history, interviewer assignment, hiring recommendation, and job offer creation.

**Main roles:** Applicant, recruiter, interviewer, HR head depending on endpoint.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/applications/` | Application list scoped by role. |
| `/api/applications/<application_id>/` | Application detail scoped by role. |
| `/api/applications/<application_id>/screen/` | Recruiter-controlled AI resume screening. |
| `/api/applications/<application_id>/candidate-profile/` | Candidate profile for review. |
| `/api/applications/<application_id>/shortlist/` | Recruiter shortlist action. |
| `/api/applications/<application_id>/assign-interviewer/` | Assign interviewer. |
| `/api/applications/<application_id>/reject/` | Recruiter rejection action. |
| `/api/applications/<application_id>/remark/` | Recruiter remark. |
| `/api/applications/<application_id>/status-history/` | Application status history. |
| `/api/applications/<application_id>/hiring-decision/` | Recruiter hiring recommendation. |
| `/api/applications/<application_id>/job-offer/` | Job offer creation. |

**Permission notes:** Applicants only see their own applications. Recruiters/HR heads are organization-scoped. Interviewer access is limited to assigned candidate/interview contexts.

## AI Screening and Ranking APIs

**Purpose:** Provide AI-assisted candidate screening and ranking while preserving human decision-making.

**Main roles:** Recruiter.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/applications/<application_id>/screen/` | Extracts resume information and calculates screening scores. |
| `/api/jobs/<job_id>/ranked-candidates/` | Lists ranked candidates for a job. |

**Algorithm notes:** Screening uses the documented score formula from `ALGORITHMS.md`: semantic score, skill score, experience score, and education score are combined into a final score. If optional semantic dependencies are unavailable, fallback lexical matching may be used. AI supports recruiter decisions; it does not automatically make the final hiring decision.

## Interviews APIs

**Purpose:** Manage interviews, assigned interview lists, interview details, interview invitations, recordings, and evaluations.

**Main roles:** Recruiter, interviewer, applicant.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/interviews/` | Interview list/create where permitted. |
| `/api/interviews/assigned/` | Interviewer assigned interviews. |
| `/api/interviews/<interview_id>/` | Interview detail. |
| `/api/interviews/<interview_id>/send-invitation/` | Send interview invitation. |
| `/api/interviews/<interview_id>/recordings/` | Upload interview recording. |
| `/api/interviews/<interview_id>/evaluations/` | Submit interview evaluation. |
| `/api/interviews/<interview_id>/evaluation-detail/` | Review evaluation detail. |
| `/api/interview-invitations/` | Applicant invitation list. |
| `/api/interview-invitations/<invitation_id>/accept/` | Applicant accepts invitation. |
| `/api/interview-invitations/<invitation_id>/decline/` | Applicant declines invitation. |

**Permission notes:** Interviewers are limited to assigned interviews/candidates. Applicants can only access their own invitations.

## Interview Recordings, Transcripts, and AI Summaries

**Purpose:** Upload recordings, generate/review transcripts, generate AI summaries, and edit summary records.

**Main roles:** Interviewer, with organization/assignment checks.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/interviews/<interview_id>/recordings/` | Upload recording for an interview. |
| `/api/recordings/<recording_id>/transcribe/` | Generate transcript. |
| `/api/transcripts/<transcript_id>/generate-summary/` | Generate AI summary. |
| `/api/interview-summaries/<summary_id>/` | Update/review summary data. |

**Fallback notes:** Transcription and summary generation can run with mock/demo fallback behavior when real external AI/ASR keys are not configured.

## Hiring Decisions APIs

**Purpose:** Let recruiters submit hiring recommendations and HR heads approve or reject them.

**Main roles:** Recruiter and HR head.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/applications/<application_id>/hiring-decision/` | Recruiter submits hiring recommendation. |
| `/api/hiring-decisions/pending/` | HR head views pending decisions. |
| `/api/hiring-decisions/<decision_id>/` | Hiring decision detail. |
| `/api/hiring-decisions/<decision_id>/approve/` | HR-head approval. |
| `/api/hiring-decisions/<decision_id>/reject/` | HR-head rejection. |

**Permission notes:** HR-head actions are organization-scoped. Final approval remains a human workflow decision.

## Job Offers APIs

**Purpose:** Create job offers after hiring approval and allow applicants to respond.

**Main roles:** Recruiter, HR head, applicant depending on endpoint.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/applications/<application_id>/job-offer/` | Create offer. |
| `/api/job-offers/` | List offers scoped by role. |
| `/api/job-offers/<offer_id>/accept/` | Applicant accepts offer. |
| `/api/job-offers/<offer_id>/decline/` | Applicant declines offer. |

**Permission notes:** Applicants only respond to their own offers. Organization staff access is scoped to their organization.

## Notifications APIs

**Purpose:** Provide role-scoped notifications and read/unread status.

**Main roles:** Applicant, recruiter, interviewer, HR head.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/notifications/` | Notification list. |
| `/api/notifications/read-all/` | Mark all notifications as read. |
| `/api/notifications/unread-count/` | Unread count. |
| `/api/notifications/<notification_id>/read/` | Mark one notification as read. |

**Permission notes:** Users can only access their own notifications.

## Analytics and PDF Reports APIs

**Purpose:** Provide dashboards, organization overview, job funnel analytics, and PDF report exports.

**Main roles:** Recruiter, interviewer, HR head.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/analytics/recruiter/dashboard/` | Recruiter dashboard metrics. |
| `/api/analytics/interviewer/dashboard/` | Interviewer dashboard metrics. |
| `/api/analytics/hr-head/dashboard/` | HR-head dashboard metrics. |
| `/api/analytics/jobs/<job_id>/funnel/` | Job funnel analytics. |
| `/api/analytics/organization/overview/` | Organization overview analytics. |
| `/api/reports/recruiter-summary.pdf` | Recruiter PDF report. |
| `/api/reports/interviewer-summary.pdf` | Interviewer PDF report. |
| `/api/reports/hr-head-summary.pdf` | HR-head PDF report. |

**Permission notes:** Analytics are role-protected and organization-scoped where applicable. PDF export requires the backend environment and ReportLab dependency to be installed.

## Billing and Subscription APIs

**Purpose:** Manage subscription plans, current subscription, invoices, upgrades, demo payment success, and optional Stripe checkout/webhook support.

**Main roles:** HR head for protected subscription actions. Stripe webhook endpoint is public for gateway callbacks.

**Confirmed example endpoints:**

| Endpoint | Notes |
| --- | --- |
| `/api/billing/plans/` | List subscription plans. |
| `/api/billing/subscribe/` | Subscribe using demo/local flow. |
| `/api/billing/subscription/` | Current subscription. |
| `/api/billing/upgrade/` | Upgrade subscription. |
| `/api/billing/invoices/` | Invoice list. |
| `/api/billing/checkout-sessions/` | Optional Stripe checkout session creation when configured. |
| `/api/billing/webhooks/stripe/` | Stripe webhook callback endpoint. |
| `/api/billing/demo-payment-success/` | Demo payment success endpoint. |

**Permission notes:** HR-head subscription actions are organization-scoped. Demo payment should be used for FYP unless real gateway credentials are configured.
