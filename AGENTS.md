# Instructions for Codex / AI Coding Agents

This file contains repository-level instructions for any AI coding agent working on HRRecruit.

## Project Context

HRRecruit is a Final Year Project (FYP) for an AI-powered recruitment management SaaS.

The system contains:

- Django REST Framework backend
- PostgreSQL database
- React.js web portal for Recruiter, Interviewer, and HR Department Head
- Flutter mobile app for Job Applicant
- AI resume screening and ranking
- Interview transcription and AI summary
- Hiring decision and HR approval workflow
- Notifications
- Analytics and reporting
- Subscription and billing

## Source of Truth

Use the written FYP requirements and the markdown files in this repository as the implementation source of truth.

Do **not** follow Chapter 4 ERD, UML, use case, sequence, or process diagrams because they are incorrect.

Only Chapter 4 UI design screens may be used as visual reference.

If there is any conflict between the full FYP report and these markdown files, follow these markdown files first.

## Development Rules

Build the project incrementally. Do not generate the whole system in one task.

After each task:

1. List changed files.
2. Explain what was implemented.
3. Provide exact commands to run.
4. Provide manual testing steps.
5. Avoid modifying unrelated files.

## Technical Rules

Use:

- Django REST Framework for backend APIs
- PostgreSQL from the start
- `djangorestframework-simplejwt` for JWT authentication
- `django-cors-headers` for CORS
- `python-dotenv` for environment variables
- Local media storage at the beginning
- Django `BigAutoField` primary keys

Do **not** use these unless a prompt explicitly requests them:

- Redis
- Celery
- AWS S3
- Firebase Cloud Messaging
- SendGrid
- Stripe / PayPal / FPX real payment integration
- Google Calendar OAuth
- LinkedIn OAuth
- Real OpenAI API calls

For early development, use:

- Console email backend
- Database-backed OTP
- Demo payment flow
- Local media storage
- Mock transcription
- Mock AI summary
- Optional mock semantic matching if `sentence-transformers` is not installed

## Backend App Names

Use these Django apps inside `backend/apps/`:

- `users`
- `organizations`
- `jobs`
- `applications`
- `interviews`
- `evaluations`
- `hiring`
- `notifications`
- `analytics`
- `billing`
- `ai_services`

## Role Names

Use these role values exactly:

- `applicant`
- `recruiter`
- `interviewer`
- `hr_head`

## Security Rules

Every protected API must require authentication.

Role-based permissions must be enforced.

Organization data isolation must be enforced:

- Recruiters can only access their own organization's data.
- Interviewers can only access assigned interviews or assigned candidates.
- HR heads can only access their own organization's data.
- Applicants can only access their own profile, applications, invitations, offers, and notifications.

File uploads must validate:

- File type
- File size
- User permission
- Related object ownership

API errors should return clean JSON responses and should not expose stack traces.

## AI Rules

AI should support human decision-making. It should not automatically make final hiring decisions.

For resume screening:

- Extract resume text.
- Extract skills, experience, and education.
- Calculate semantic score.
- Calculate skill score.
- Calculate experience score.
- Calculate education score.
- Calculate final score.

Use this formula:

```text
final_score = 0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score
```

If the score is below the threshold, mark the application as `screened_not_qualified`.

Do not automatically reject the applicant. The recruiter must make the final shortlist/reject decision.

## Algorithm Implementation Rule

AI-related features must follow `ALGORITHMS.md`.

The implementation should follow these five algorithm groups:

1. spaCy-based resume extraction
2. Sentence-BERT resume-job semantic matching
3. Hybrid candidate ranking formula
4. Interview audio transcription
5. AI interview summarization

For resume extraction, standard spaCy `en_core_web_sm` may be combined with PhraseMatcher, skill dictionaries, keyword rules, and regex patterns to make the algorithm practical for FYP implementation.

AI must support recruiter/interviewer decision-making. It must not automatically make final hiring decisions.

## Testing Rules

Add tests for important business flows, not just individual functions.

Mock external services.

Do not call real external APIs during tests.
