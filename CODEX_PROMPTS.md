# HRRecruit Codex Prompts

Use these prompts one by one.

Do not skip directly to later prompts.

After each prompt, run the project, test the feature, and commit the working changes.

## Global Instruction to Add When Needed

```text
Important project rules:
- This is a fresh HRRecruit FYP project.
- Use the written FYP requirements and markdown files in this repository as the source of truth.
- Do not follow Chapter 4 ERD, UML, use case, sequence, or process diagrams because they are incorrect.
- Only Chapter 4 UI design screens may be used as visual reference.
- Use PostgreSQL from the start.
- Use Django BigAutoField primary keys, not UUIDs.
- Keep the implementation simple and runnable locally first.
- Do not add Redis, Celery, S3, Firebase, SendGrid, Stripe, Google Calendar OAuth, LinkedIn OAuth, or real OpenAI API calls unless this prompt explicitly asks for them.
- After making changes, list changed files and provide exact commands to run.
```

---

## Prompt 1 — Backend Foundation

```text
Create the backend foundation for HRRecruit.

Important project rules:
- This is a fresh project from absolute zero.
- Use the written FYP requirements and markdown files in this repository as the source of truth.
- Do not follow Chapter 4 ERD, UML, use case, sequence, or process diagrams because they are incorrect.
- Only Chapter 4 UI design screens may be used as visual reference later.
- Use PostgreSQL from the start.
- Use Django REST Framework.
- Use django-cors-headers.
- Use djangorestframework-simplejwt.
- Use python-dotenv for environment variables.
- Use local media storage.
- Use BigAutoField primary keys.
- Do not create feature apps yet.
- Do not create React or Flutter code yet.
- Do not add Redis, Celery, S3, Firebase, SendGrid, Stripe, Google Calendar, LinkedIn OAuth, or OpenAI yet.

Create this structure:
- backend/
- backend/config/
- backend/manage.py
- backend/requirements.txt
- backend/.env.example
- backend/.gitignore

Configure:
- PostgreSQL database settings using .env
- INSTALLED_APPS with Django default apps, rest_framework, corsheaders, and simplejwt only
- MEDIA_URL and MEDIA_ROOT
- CORS for local React development later
- REST_FRAMEWORK default JWT authentication

After implementation, provide:
1. PostgreSQL database creation command
2. Python virtual environment command
3. pip install command
4. migrate command
5. runserver command
6. list of changed files
```

---

## Prompt 2 — Create Django Apps

```text
Create the Django apps for HRRecruit inside backend/apps/.

Apps to create:
- users
- organizations
- jobs
- applications
- interviews
- evaluations
- hiring
- notifications
- analytics
- billing
- ai_services

Requirements:
- Register the apps in INSTALLED_APPS.
- Configure AppConfig for each app.
- Do not create models yet.
- Do not create serializers, views, URLs, or permissions yet.
- Make sure imports and app labels are correct.
- Make sure the backend still runs after app creation.

After implementation, provide:
1. list of changed files
2. command to check the project
3. command to run the server
```

---

## Prompt 3 — Custom User Model

```text
Implement only the custom User model for HRRecruit.

Important:
- Do this before other business models.
- Use AbstractBaseUser and PermissionsMixin.
- Use email as USERNAME_FIELD.
- Use BigAutoField primary key.
- Use role choices:
  - applicant
  - recruiter
  - interviewer
  - hr_head
- Do not create organization, job, application, interview, hiring, billing, analytics, notification, or AI models yet.

Fields:
- email
- full_name
- phone_number
- role
- is_active
- is_staff
- date_joined

Also implement:
- CustomUserManager
- admin registration
- AUTH_USER_MODEL setting
- basic __str__ method
- migrations

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
4. createsuperuser command
5. how to verify the user appears in Django admin
```

---

## Prompt 4 — User Profiles

```text
Implement user profile models for HRRecruit.

Models:
1. ApplicantProfile
   - user OneToOneField to User
   - linkedin_url
   - personal_summary
   - resume_file
   - created_at
   - updated_at

2. RecruiterProfile
   - user OneToOneField to User
   - created_at
   - updated_at

3. InterviewerProfile
   - user OneToOneField to User
   - created_at
   - updated_at

4. HRHeadProfile
   - user OneToOneField to User
   - created_at
   - updated_at

Requirements:
- Use local media storage for resume files.
- Validate resume upload extension later in serializer, not in model.
- Register models in admin.
- Do not create organization or job models yet.
- Create profile automatically when user is created based on role using a clean method or signal.

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
4. simple manual testing steps in Django shell
```

---

## Prompt 5 — Authentication APIs

```text
Implement authentication APIs for HRRecruit.

Endpoints:
- POST /api/auth/register/
- POST /api/auth/login/
- POST /api/auth/logout/
- GET /api/auth/profile/
- PATCH /api/auth/profile/
- POST /api/auth/password-reset/request/
- POST /api/auth/password-reset/confirm/
- POST /api/auth/resume/upload/

Requirements:
- Use JWT using djangorestframework-simplejwt.
- Applicant self-registration should create a user with role applicant.
- For now, recruiter/interviewer/hr_head accounts will be created later by HR head or admin.
- Use database-backed OTP model instead of Redis for now.
- OTP should be 6 digits and expire in 10 minutes.
- Use console email backend for now.
- Resume upload should accept PDF and DOCX only.
- Resume upload max size: 5MB.
- Return clean JSON responses.
- Do not implement LinkedIn OAuth yet.
- Do not add SendGrid yet.

Also create:
- serializers.py
- views.py
- urls.py under users app
- include users URLs in config/urls.py

After implementation, provide:
1. list of changed files
2. migrate command if needed
3. Postman test examples for register, login, profile, and resume upload
```

---

## Prompt 6 — Permissions

```text
Create role-based permission classes for HRRecruit.

Permission classes:
- IsApplicant
- IsRecruiter
- IsInterviewer
- IsHRHead
- IsRecruiterOrHRHead
- IsOrganizationMember

Requirements:
- Place them in a suitable permissions.py file.
- Permissions should be reusable across all apps.
- For now, organization isolation can be prepared but not fully used until the Organization model exists.
- Do not change existing auth endpoints unless needed.
- Do not create business models yet.

After implementation, provide:
1. list of changed files
2. explanation of how each permission is used
3. sample usage in a DRF view
```

---

## Prompt 7 — Organization Models

```text
Implement organization and team setup models.

Models:
1. Organization
   - name
   - registration_no
   - email
   - contact_number
   - address
   - status: pending, active, suspended, deleted
   - created_by FK to User
   - created_at
   - updated_at

2. OrganizationMembership
   - organization FK
   - user FK
   - role: hr_head, recruiter, interviewer
   - status: active, inactive
   - joined_at

Requirements:
- One HR head can create an organization.
- Recruiters and interviewers belong to an organization through OrganizationMembership.
- Applicants do not need to belong to an organization.
- Register models in admin.
- Do not implement subscription yet.
- Do not implement payments yet.

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
4. admin testing steps
```

---

## Prompt 8 — Organization APIs

```text
Implement organization and team setup APIs.

Endpoints:
- POST /api/org/create/
- GET /api/org/
- PATCH /api/org/
- DELETE /api/org/
- POST /api/org/members/
- GET /api/org/members/
- GET /api/org/members/?search=
- PATCH /api/org/members/{id}/deactivate/
- POST /api/org/members/bulk/

Requirements:
- Only HR head can create and manage organization.
- When HR head creates organization, create OrganizationMembership for that HR head.
- For company registration verification, use a mock function for now.
- For organization deletion, use OTP confirmation if possible; otherwise mark TODO and implement soft delete.
- HR head can create recruiter and interviewer accounts.
- Bulk import should support CSV first.
- Excel bulk import can be added later.
- Temporary passwords should be generated and printed through console email backend.
- Do not add SendGrid yet.

After implementation, provide:
1. list of changed files
2. URL list
3. Postman examples for creating organization and creating recruiter/interviewer
```

---

## Prompt 9 — Job Models

```text
Implement job posting and requirement configuration models.

Models:
1. JobPosting
   - organization FK
   - recruiter FK to User
   - title
   - description
   - employment_type
   - approximate_salary
   - location
   - status: draft, open, closed
   - created_at
   - updated_at

2. JobRequirement
   - job FK
   - requirement_type: skill, experience, education, certification, other
   - description
   - weight_score
   - minimum_threshold
   - created_at

3. InterviewEvaluationForm
   - job FK OneToOneField
   - title
   - created_at

4. EvaluationCriterion
   - form FK
   - criterion_name
   - description
   - max_score
   - weight_score
   - created_at

5. SavedJobPosting
   - applicant FK to User
   - job FK
   - saved_at
   - unique applicant + job

Requirements:
- Use BigAutoField primary keys.
- Register models in admin.
- Validate weight sums later in serializers.
- Do not implement job APIs yet.

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
```

---

## Prompt 10 — Job APIs

```text
Implement job posting APIs.

Endpoints:
- POST /api/jobs/
- GET /api/jobs/
- GET /api/jobs/{id}/
- PATCH /api/jobs/{id}/
- DELETE /api/jobs/{id}/
- POST /api/jobs/{id}/duplicate/
- POST /api/jobs/{id}/requirements/
- POST /api/jobs/{id}/eval-form/
- POST /api/jobs/{id}/save/
- DELETE /api/jobs/{id}/save/
- GET /api/jobs/saved/

Requirements:
- Recruiters can create/manage jobs only for their own organization.
- HR heads can view jobs in their organization.
- Applicants can view only open jobs.
- Applicants can search/filter open jobs by title, location, employment_type.
- Job requirements can be created with weights.
- Validate that requirement weights sum to 1.0, or normalize only if explicitly requested.
- Evaluation form criteria can be created for a job.
- Applicants can save/unsave jobs.
- Do not enforce subscription limits yet; leave a clear TODO hook.

After implementation, provide:
1. list of changed files
2. endpoint list
3. Postman examples for recruiter and applicant flows
```

---

## Prompt 11 — Application Models

```text
Implement job application models.

Models:
1. JobApplication
   - job FK
   - applicant FK to User
   - status with choices:
     submitted
     withdrawn
     screened
     screened_qualified
     screened_not_qualified
     shortlisted
     rejected
     interview_invited
     interview_accepted
     interview_declined
     interviewing
     evaluation_submitted
     decision_pending
     hr_approved
     hr_rejected
     offer_sent
     offer_accepted
     offer_declined
     hired
   - recruiter_remark
   - semantic_score nullable
   - skill_score nullable
   - experience_score nullable
   - education_score nullable
   - final_score nullable
   - score_explanation JSONField default dict
   - applied_at
   - updated_at
   - unique applicant + job

2. ApplicationStageHistory
   - application FK
   - from_stage
   - to_stage
   - changed_by FK to User nullable
   - note
   - changed_at

Requirements:
- Register in admin.
- Add helper method to change status and create stage history.
- Do not implement AI screening yet.
- Do not implement interview models yet.

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
```

---

## Prompt 12 — Application APIs

```text
Implement job application APIs.

Endpoints:
- POST /api/jobs/{id}/apply/
- DELETE /api/jobs/{id}/apply/
- GET /api/applications/
- GET /api/applications/{id}/
- GET /api/applications/{id}/status-history/

Requirements:
- Applicants can apply only to open jobs.
- Applicants cannot apply twice to the same job.
- Applicants can withdraw only when status is submitted or screened.
- Applicants can view only their own applications.
- Recruiters can view applications only for jobs they created within their organization.
- HR heads can view applications within their organization.
- Every status change must create ApplicationStageHistory.
- Do not trigger AI screening automatically yet.
- Add a placeholder service call or TODO for AI screening.

After implementation, provide:
1. list of changed files
2. endpoint list
3. Postman examples for applicant apply and recruiter view
```

---

## Prompt 13 — AI Services Foundation

```text
Create the AI services foundation for HRRecruit.

Inside ai_services app, create service files:
- resume_text_extractor.py
- skill_extractor.py
- semantic_matcher.py
- scoring.py

Requirements:
- resume_text_extractor.py should support extracting text from PDF and DOCX using local files.
- skill_extractor.py should use a simple predefined skills dictionary and basic normalization.
- semantic_matcher.py should contain a function for semantic similarity, but for now allow a fallback mock score if sentence-transformers is not installed.
- scoring.py should calculate:
  final_score = 0.4 semantic_score + 0.3 skill_score + 0.2 experience_score + 0.1 education_score
- Do not call OpenAI.
- Do not use Celery.
- Do not use S3.
- Keep the service functions independently testable.

After implementation, provide:
1. list of changed files
2. how to test each service in Django shell
```

---

## Prompt 14 — AI Resume Screening API

```text
Implement AI resume screening for job applications.

Endpoint:
- POST /api/applications/{id}/screen/

Requirements:
- Only the recruiter who owns the job can run screening.
- Use the applicant's uploaded resume.
- Extract resume text.
- Extract skills using the skill dictionary service.
- Compare extracted resume information against job description and job requirements.
- Calculate:
  - semantic_score
  - skill_score
  - experience_score
  - education_score
  - final_score
  - score_explanation
- Save all scores to JobApplication.
- Change status to screened_qualified if final_score >= 60.
- Change status to screened_not_qualified if final_score < 60.
- Do not automatically reject the applicant.
- Create ApplicationStageHistory.
- Return the score breakdown in JSON.

Do not use Celery yet.
Do not use OpenAI yet.

After implementation, provide:
1. list of changed files
2. Postman example
3. sample expected response
```

---

## Prompt 15 — Candidate Ranking and Shortlisting APIs

```text
Implement candidate ranking and shortlisting APIs.

Endpoints:
- GET /api/jobs/{id}/ranked-candidates/
- GET /api/applications/{id}/candidate-profile/
- POST /api/applications/{id}/shortlist/
- POST /api/applications/{id}/reject/
- PATCH /api/applications/{id}/remark/

Requirements:
- Recruiter can only access candidates for own job postings.
- Ranked candidates should be ordered by final_score descending.
- Candidate profile should include applicant profile, resume info, extracted skills if available, scores, and application status.
- Shortlist requires assigning an interviewer from the same organization.
- Reject requires a reason or remark.
- Add remark should be visible later to assigned interviewer.
- Every action should update status and create ApplicationStageHistory.
- Do not create interview invitation yet, only prepare assignment if needed.

After implementation, provide:
1. list of changed files
2. endpoint list
3. Postman examples
```

---

## Prompt 16 — Interview Models

```text
Implement interview management models.

Models:
1. Interview
   - application FK
   - organization FK
   - recruiter FK to User
   - interviewer FK to User nullable
   - scheduled_datetime nullable
   - mode: online, physical, phone
   - meeting_link
   - location
   - status: assigned, invitation_sent, scheduled, declined, completed, cancelled
   - created_at
   - updated_at

2. InterviewInvitation
   - interview FK
   - proposed_datetime
   - mode
   - meeting_link
   - location
   - status: pending, accepted, declined, expired
   - decline_reason
   - sent_at
   - responded_at

3. InterviewStatusHistory
   - interview FK
   - from_status
   - to_status
   - changed_by FK to User nullable
   - note
   - changed_at

4. CalendarEvent
   - interview FK
   - provider
   - external_event_id blank
   - calendar_link blank
   - last_synced_at nullable
   - sync_status: not_synced, synced, failed

Requirements:
- Register in admin.
- Use single interviewer for FYP MVP.
- Do not implement Google Calendar OAuth yet.
- CalendarEvent is only a local sync stub for now.

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
```

---

## Prompt 17 — Interview APIs

```text
Implement interview management APIs.

Endpoints:
- GET /api/interviews/assigned/
- POST /api/applications/{id}/assign-interviewer/
- POST /api/interviews/{id}/send-invitation/
- GET /api/interview-invitations/
- POST /api/interview-invitations/{id}/accept/
- POST /api/interview-invitations/{id}/decline/
- GET /api/interviews/
- GET /api/interviews/{id}/

Requirements:
- Recruiter assigns interviewer from same organization.
- Interviewer can view assigned applicants/interviews.
- Interviewer sends invitation to applicant.
- Applicant can view received invitations.
- Applicant can accept or decline.
- Accepting invitation updates interview scheduled_datetime and status.
- Declining invitation stores decline_reason and updates status.
- Create InterviewStatusHistory for status changes.
- Create in-app notifications using a placeholder function if Notification model is not ready.
- Do not send real email yet.
- Do not sync Google Calendar yet.
- Generate a calendar_link placeholder if possible.

After implementation, provide:
1. list of changed files
2. endpoint list
3. Postman examples for full invitation flow
```

---

## Prompt 18 — Evaluation Models

```text
Implement interview evaluation models.

Models:
1. InterviewRecording
   - interview FK
   - audio_file
   - uploaded_by FK to User
   - uploaded_at

2. InterviewTranscript
   - recording FK
   - transcript_text
   - transcript_json JSONField default dict
   - generated_at

3. InterviewAISummary
   - transcript FK
   - strengths
   - weaknesses
   - communication_score
   - overall_impression
   - editable_summary_text
   - edited_by FK to User nullable
   - generated_at
   - updated_at

4. InterviewEvaluation
   - interview FK
   - interviewer FK to User
   - total_score
   - overall_comment
   - submitted_at

5. EvaluationAnswer
   - evaluation FK
   - criterion FK to EvaluationCriterion
   - score
   - comment

Requirements:
- Register in admin.
- Use local media storage for audio files.
- Do not call OpenAI or Whisper yet.
- Do not implement APIs yet.

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
```

---

## Prompt 19 — Evaluation APIs with Mock AI

```text
Implement interview evaluation APIs with mock transcription and mock AI summary first.

Endpoints:
- POST /api/interviews/{id}/recordings/
- POST /api/recordings/{id}/transcribe/
- POST /api/transcripts/{id}/generate-summary/
- PATCH /api/interview-summaries/{id}/
- POST /api/interviews/{id}/evaluations/
- GET /api/interviews/{id}/evaluation-detail/

Requirements:
- Only assigned interviewer can upload recording and submit evaluation.
- Recruiter who owns the application can view evaluation detail.
- Audio upload should validate file type and size.
- Transcription should use a mock service for now:
  "This is a mock transcript for FYP development."
- AI summary should use a mock service for now with strengths, weaknesses, communication_score, and overall_impression.
- Interviewer can edit AI summary before final evaluation submission.
- Evaluation answers should follow the job's EvaluationCriterion records.
- Calculate total_score from answers.
- After submission, update application status to evaluation_submitted.
- Create notifications using placeholder function if needed.

Do not use real OpenAI Whisper yet.
Do not use GPT API yet.

After implementation, provide:
1. list of changed files
2. endpoint list
3. Postman examples
```

---

## Prompt 20 — Hiring Models

```text
Implement hiring decision and job offer models.

Models:
1. HiringDecision
   - application FK
   - recruiter FK to User
   - decision: hire, reject
   - recruiter_justification
   - status: pending_hr_approval, approved, rejected
   - hr_head FK to User nullable
   - hr_head_justification
   - submitted_at
   - reviewed_at

2. JobOffer
   - application FK
   - offer_letter_file nullable
   - offer_message
   - offer_status: sent, accepted, declined, expired
   - respond_deadline
   - sent_at
   - responded_at

Requirements:
- Register in admin.
- Do not implement APIs yet.

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
```

---

## Prompt 21 — Hiring APIs

```text
Implement hiring decision and approval workflow APIs.

Endpoints:
- POST /api/applications/{id}/hiring-decision/
- GET /api/hiring-decisions/pending/
- POST /api/hiring-decisions/{id}/approve/
- POST /api/hiring-decisions/{id}/reject/
- GET /api/hiring-decisions/{id}/
- POST /api/applications/{id}/job-offer/
- GET /api/job-offers/
- POST /api/job-offers/{id}/accept/
- POST /api/job-offers/{id}/decline/

Requirements:
- Recruiter submits hire/reject decision with justification.
- HR head can view pending decisions in own organization.
- HR head approves or rejects with justification.
- If HR approves a hire decision, recruiter can send job offer.
- Applicant can accept or decline job offer.
- Every step updates JobApplication status.
- Every status change creates ApplicationStageHistory.
- Create notifications for recruiter, HR head, and applicant where appropriate.
- Do not send real email yet.

After implementation, provide:
1. list of changed files
2. endpoint list
3. Postman examples for recruiter → HR head → applicant flow
```

---

## Prompt 22 — Notifications

```text
Implement database-backed in-app notifications.

Model:
Notification
- recipient FK to User
- notification_type
- title
- message
- related_entity_type
- related_entity_id
- is_read
- created_at

Endpoints:
- GET /api/notifications/
- PATCH /api/notifications/{id}/read/
- PATCH /api/notifications/read-all/
- GET /api/notifications/unread-count/

Requirements:
- Create a notification service function:
  create_notification(recipient, notification_type, title, message, related_entity=None)
- Replace placeholder notification calls in previous modules with this service.
- Do not add Firebase yet.
- Do not add SendGrid yet.

After implementation, provide:
1. list of changed files
2. endpoint list
3. places where notifications are triggered
```

---

## Prompt 23 — Analytics APIs

```text
Implement analytics APIs for HRRecruit.

Endpoints:
- GET /api/analytics/recruiter/dashboard/
- GET /api/analytics/interviewer/dashboard/
- GET /api/analytics/hr-head/dashboard/
- GET /api/analytics/jobs/{id}/funnel/
- GET /api/analytics/organization/overview/

Metrics:
- total job postings
- total applications
- applications by status
- shortlisted count
- rejected count
- hired count
- average time-to-hire
- dropout rate
- offer acceptance rate
- interviewer evaluation count
- recruiter hire count
- candidate funnel data

Requirements:
- Use existing database data.
- Only allow access to data within user's organization.
- Applicants should not access analytics.
- Return JSON suitable for Chart.js.
- Do not implement PDF export yet.

After implementation, provide:
1. list of changed files
2. endpoint list
3. sample JSON response for each dashboard
```

---

## Prompt 24 — PDF Export

```text
Implement PDF report export for HRRecruit analytics.

Endpoints:
- GET /api/reports/recruiter-summary.pdf
- GET /api/reports/interviewer-summary.pdf
- GET /api/reports/hr-head-summary.pdf

Requirements:
- Use ReportLab.
- Generate simple but readable PDF reports.
- Include title, generated date, user/organization info, and key metrics.
- Enforce organization isolation.
- Applicants cannot export analytics reports.
- Do not generate complex charts inside PDF yet; use text/table format.

After implementation, provide:
1. list of changed files
2. endpoint list
3. how to test PDF download in browser/Postman
```

---

## Prompt 25 — Billing Models

```text
Implement subscription and billing models.

Models:
1. SubscriptionPlan
   - name: Basic, Pro, Enterprise
   - max_job_postings
   - billing_cycle: monthly, yearly
   - price
   - features_description
   - is_active

2. Subscription
   - organization FK
   - plan FK
   - start_date
   - end_date
   - status: active, expired, cancelled
   - is_auto_renew
   - created_at

3. Payment
   - subscription FK
   - payment_gateway: demo, stripe, paypal, fpx
   - transaction_reference
   - amount
   - currency
   - status
   - paid_at
   - invoice_number

Requirements:
- Register in admin.
- Add a seed command to create Basic, Pro, and Enterprise plans.
- Do not implement real Stripe/PayPal/FPX yet.
- Do not implement APIs yet.

After implementation, provide:
1. list of changed files
2. makemigrations command
3. migrate command
4. seed command usage
```

---

## Prompt 26 — Billing APIs

```text
Implement subscription and demo billing APIs.

Endpoints:
- GET /api/billing/plans/
- POST /api/billing/subscribe/
- GET /api/billing/subscription/
- POST /api/billing/upgrade/
- GET /api/billing/invoices/
- POST /api/billing/demo-payment-success/

Requirements:
- HR head can select a plan.
- Use demo payment flow only.
- demo-payment-success should activate subscription and create Payment record.
- Generate invoice_number automatically.
- HR head can view invoice/payment history.
- Implement subscription plan enforcement:
  recruiter cannot create more open job postings than max_job_postings.
- Add this enforcement to job creation endpoint.
- Do not integrate real payment gateways yet.

After implementation, provide:
1. list of changed files
2. endpoint list
3. Postman examples
4. how to test job posting limit enforcement
```

---

## Prompt 27 — Backend Tests

```text
Add backend tests for the current HRRecruit system.

Use Django TestCase and DRF APIClient.

Test areas:
1. Applicant registration and JWT login
2. HR head organization creation
3. HR head creates recruiter/interviewer
4. Recruiter creates job posting
5. Applicant views open jobs
6. Applicant applies for job
7. Recruiter screens application
8. Recruiter views ranked candidates
9. Recruiter assigns interviewer
10. Interviewer sends invitation
11. Applicant accepts/declines invitation
12. Interviewer uploads recording and submits evaluation
13. Recruiter submits hiring decision
14. HR head approves/rejects decision
15. Recruiter sends offer
16. Applicant accepts/declines offer
17. Notification unread count
18. Subscription plan limit

Requirements:
- Mock AI services.
- Do not call external APIs.
- Tests should be runnable with python manage.py test.
- Focus on important business flows, not 100% coverage.

After implementation, provide:
1. list of changed files
2. test command
3. explanation of what is covered
```

---

## Prompt 28 — React Setup

```text
Create the React web portal for HRRecruit.

Requirements:
- Create web/ using Vite React.
- Install:
  - axios
  - react-router-dom
  - zustand
  - chart.js
  - react-chartjs-2
  - @mui/material
  - @emotion/react
  - @emotion/styled
- Configure basic folder structure:
  - src/api/
  - src/components/
  - src/layouts/
  - src/pages/auth/
  - src/pages/recruiter/
  - src/pages/interviewer/
  - src/pages/hr_head/
  - src/store/
  - src/routes/
- Add Axios instance with base URL from .env.
- Do not build full pages yet.
- Do not implement applicant mobile features in React.

After implementation, provide:
1. list of changed files
2. npm install command
3. npm run dev command
```

---

## Prompt 29 — React Auth

```text
Implement React authentication and route guards.

Pages:
- LoginPage
- RegisterApplicantPage
- ProfilePage

Requirements:
- Use backend JWT login.
- Store access and refresh token safely for development using localStorage.
- Add Axios interceptor to attach access token.
- Add role-based route guards for recruiter, interviewer, and hr_head.
- Add logout function.
- Add simple dashboard redirect based on role.
- Do not implement full dashboards yet.

After implementation, provide:
1. list of changed files
2. routes created
3. how to test login for each role
```

---

## Prompt 30 — React HR Head Portal

```text
Implement HR head web portal pages.

Pages:
- HRHeadDashboardPage
- OrganizationProfilePage
- TeamMembersPage
- CreateTeamMemberPage
- BulkImportMembersPage
- PendingHiringDecisionsPage
- BillingPage
- HRAnalyticsPage
- NotificationsPage

Requirements:
- Use existing backend APIs.
- HR head can create/update organization.
- HR head can create recruiter/interviewer accounts.
- HR head can search/deactivate members.
- HR head can approve/reject hiring decisions.
- HR head can select subscription plan and simulate payment.
- HR head can view analytics.
- Keep UI simple and clean.
- Use Chapter 4 UI design screens only as visual reference if useful.

After implementation, provide:
1. list of changed files
2. routes added
3. backend endpoints used by each page
```

---

## Prompt 31 — React Recruiter Portal

```text
Implement recruiter web portal pages.

Pages:
- RecruiterDashboardPage
- JobListPage
- JobCreateEditPage
- JobDetailPage
- JobRequirementsPage
- EvaluationFormBuilderPage
- ApplicationsPage
- CandidateRankingPage
- CandidateProfilePage
- InterviewAssignmentPage
- InterviewEvaluationDetailPage
- HiringDecisionPage
- JobOfferPage
- RecruiterAnalyticsPage
- NotificationsPage

Requirements:
- Recruiter can create/edit/delete/duplicate jobs.
- Recruiter can configure requirements and evaluation criteria.
- Recruiter can view applications.
- Recruiter can run AI screening.
- Recruiter can view ranked candidates.
- Recruiter can shortlist/reject candidates.
- Recruiter can assign interviewer.
- Recruiter can view submitted interview evaluation and AI summary.
- Recruiter can submit hiring decision.
- Recruiter can send job offer after HR approval.
- Use existing backend APIs.
- Keep UI practical for FYP demo.

After implementation, provide:
1. list of changed files
2. routes added
3. backend endpoints used by each page
```

---

## Prompt 32 — React Interviewer Portal

```text
Implement interviewer web portal pages.

Pages:
- InterviewerDashboardPage
- AssignedCandidatesPage
- CandidateDetailPage
- SendInvitationPage
- InterviewListPage
- InterviewDetailPage
- UploadRecordingPage
- TranscriptSummaryPage
- SubmitEvaluationPage
- InterviewerAnalyticsPage
- NotificationsPage

Requirements:
- Interviewer can view assigned candidates.
- Interviewer can send interview invitation.
- Interviewer can view invitation response status.
- Interviewer can view upcoming/completed interviews.
- Interviewer can upload audio recording.
- Interviewer can generate mock transcript and AI summary.
- Interviewer can edit AI summary.
- Interviewer can submit evaluation answers.
- Use existing backend APIs.

After implementation, provide:
1. list of changed files
2. routes added
3. backend endpoints used by each page
```

---

## Prompt 33 — React Analytics Polish

```text
Improve analytics UI in the React web portal.

Requirements:
- Use Chart.js / react-chartjs-2.
- Add charts for:
  - applications by status
  - candidate funnel
  - time-to-hire
  - offer acceptance rate
  - recruiter/interviewer performance
- Add PDF export buttons.
- Keep charts simple and readable.
- Use backend analytics endpoints.
- Do not add unnecessary complex UI libraries.

After implementation, provide:
1. list of changed files
2. charts added
3. backend endpoints used
```

---

## Prompt 34 — Flutter Setup

```text
Create the Flutter mobile app for HRRecruit applicants.

Requirements:
- Create mobile/ using flutter create.
- Add dependencies:
  - dio
  - flutter_secure_storage
  - go_router
  - provider or riverpod
  - file_picker
  - url_launcher
- Configure folder structure:
  - lib/api/
  - lib/models/
  - lib/screens/auth/
  - lib/screens/applicant/
  - lib/widgets/
  - lib/router/
  - lib/services/
- Add API client using Dio.
- Add secure token storage.
- Do not implement screens yet.

After implementation, provide:
1. list of changed files
2. flutter pub get command
3. flutter run command
```

---

## Prompt 35 — Flutter Auth and Profile

```text
Implement Flutter applicant authentication and profile screens.

Screens:
- LoginScreen
- RegisterScreen
- ApplicantHomeScreen
- ProfileScreen
- ResumeUploadScreen

Requirements:
- Applicant can register.
- Applicant can login.
- Store JWT using flutter_secure_storage.
- Applicant can view/edit profile.
- Applicant can upload PDF/DOCX resume.
- Add logout.
- Use existing backend APIs.

After implementation, provide:
1. list of changed files
2. screens added
3. backend endpoints used
```

---

## Prompt 36 — Flutter Jobs and Applications

```text
Implement Flutter applicant job discovery and application screens.

Screens:
- JobSearchScreen
- JobDetailScreen
- SavedJobsScreen
- MyApplicationsScreen
- ApplicationDetailScreen

Requirements:
- Applicant can search/filter open jobs.
- Applicant can view job details.
- Applicant can save/unsave jobs.
- Applicant can apply for job.
- Applicant can withdraw application if allowed.
- Applicant can view application status history.
- Use existing backend APIs.

After implementation, provide:
1. list of changed files
2. screens added
3. backend endpoints used
```

---

## Prompt 37 — Flutter Interviews, Offers, Notifications

```text
Implement Flutter applicant interview, offer, and notification screens.

Screens:
- InterviewInvitationsScreen
- InterviewInvitationDetailScreen
- MyInterviewsScreen
- JobOffersScreen
- NotificationsScreen

Requirements:
- Applicant can view interview invitations.
- Applicant can accept or decline invitations.
- Applicant can view upcoming/completed interviews.
- Applicant can view job offers.
- Applicant can accept or decline job offers.
- Applicant can view notifications and mark as read.
- Use existing backend APIs.
- Do not add Firebase push notifications yet.

After implementation, provide:
1. list of changed files
2. screens added
3. backend endpoints used
```

---

## Prompt 38 — Security Cleanup

```text
Perform security cleanup for the HRRecruit backend.

Requirements:
- Ensure all protected APIs require authentication.
- Ensure each endpoint uses correct role permission.
- Ensure organization data isolation is enforced.
- Ensure applicants cannot access recruiter/interviewer/HR head data.
- Ensure recruiters cannot access other organizations' jobs/applications.
- Ensure interviewers cannot access unassigned interviews.
- Ensure file upload validation checks extension, size, and content type where possible.
- Ensure API errors do not expose stack traces.
- Ensure settings use DEBUG from environment variable.
- Do not enable production HTTPS settings yet unless environment is production.

After implementation, provide:
1. list of changed files
2. security issues fixed
3. manual test checklist
```

---

## Prompt 39 — Optional Real OpenAI Integration

```text
Replace mock interview transcription and AI summary services with real OpenAI service integration.

Requirements:
- Keep all OpenAI code inside ai_services service files.
- Read OPENAI_API_KEY from environment variable.
- If API key is missing, fall back to mock response instead of crashing.
- Implement transcription service for audio files.
- Implement summary service that returns:
  - strengths
  - weaknesses
  - communication_score
  - overall_impression
  - editable_summary_text
- Do not scatter OpenAI calls inside views.
- Add tests using mocks.
- Do not change frontend unless necessary.

After implementation, provide:
1. list of changed files
2. required .env variables
3. how to test with and without API key
```

---

## Prompt 40 — Optional SendGrid Integration

```text
Add SendGrid email integration for HRRecruit.

Requirements:
- Keep email sending inside a notifications/email_service.py file.
- Read SENDGRID_API_KEY and DEFAULT_FROM_EMAIL from environment variables.
- If SendGrid settings are missing, fall back to console email backend.
- Send emails for:
  - OTP
  - recruiter/interviewer account creation
  - interview invitation
  - job offer
  - subscription reminder
- Do not remove database notifications.
- Add tests using mocks.

After implementation, provide:
1. list of changed files
2. required .env variables
3. test steps
```

---

## Prompt 41 — Optional Google Calendar Integration

```text
Add optional Google Calendar integration for accepted interviews.

Requirements:
- Keep calendar logic inside interviews/calendar_service.py.
- If Google OAuth credentials are missing, fall back to local CalendarEvent record only.
- For FYP demo, support creating a Google Calendar link or ICS file first.
- Do not require every user to connect Google OAuth before the interview flow can work.
- Update CalendarEvent sync_status.
- Add tests using mocks.

After implementation, provide:
1. list of changed files
2. required .env variables
3. fallback behavior
4. test steps
```

---

## Prompt 42 — Optional Real Payment Gateway

```text
Add optional real payment gateway support while keeping demo payment.

Requirements:
- Do not remove demo payment.
- Add a payment service abstraction:
  - demo
  - stripe
  - paypal
  - fpx placeholder
- Start with Stripe sandbox only.
- Read Stripe keys from environment variables.
- Create checkout session for subscription.
- Handle webhook safely.
- Create Payment record after success.
- Activate subscription after verified success.
- Add tests using mocks.

After implementation, provide:
1. list of changed files
2. required .env variables
3. webhook setup steps
4. fallback demo payment flow
```

---

# Recommended Prompt Order

```text
0. Add these markdown files to the repository.
1. Backend foundation
2. Create Django apps
3. Custom user model
4. User profiles
5. Authentication APIs
6. Permissions
7. Organization models
8. Organization APIs
9. Job models
10. Job APIs
11. Application models
12. Application APIs
13. AI services foundation
14. AI resume screening API
15. Candidate ranking and shortlisting
16. Interview models
17. Interview APIs
18. Evaluation models
19. Evaluation APIs with mock AI
20. Hiring models
21. Hiring APIs
22. Notifications
23. Analytics APIs
24. PDF export
25. Billing models
26. Billing APIs
27. Backend tests
28. React setup
29. React auth
30. React HR head portal
31. React recruiter portal
32. React interviewer portal
33. React analytics polish
34. Flutter setup
35. Flutter auth and profile
36. Flutter jobs and applications
37. Flutter interviews, offers, notifications
38. Security cleanup
39. Optional real OpenAI integration
40. Optional SendGrid integration
41. Optional Google Calendar integration
42. Optional real payment gateway
```
