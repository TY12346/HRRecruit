# HRRecruit FYP Requirements Summary

This file summarizes the corrected implementation requirements for HRRecruit.

## 1. Project Objective

Develop a web and mobile recruitment management system called HRRecruit.

The system supports the complete recruitment process:

1. Job applicants search and apply for jobs.
2. Recruiters create jobs and screen candidates.
3. AI assists resume screening and candidate ranking.
4. Interviewers manage interviews and submit evaluations.
5. AI assists interview transcription and summary generation.
6. Recruiters submit hiring decisions.
7. HR department heads approve or reject hiring decisions.
8. Applicants receive offers or rejection updates.
9. The system provides notifications, analytics, reporting, and subscription management.

## 2. Platforms

### Mobile App

Used by job applicants.

### Web Portal

Used by:

- Recruiters
- Interviewers
- HR Department Heads

### Backend API

Used by both web and mobile apps.

## 3. User and Access Management Requirements

### Applicant

- Register account
- Verify account or use OTP where applicable
- Login/logout
- Reset password
- View profile
- Edit profile
- Upload resume
- Store LinkedIn URL
- Optional mock LinkedIn import later

### Recruiter / Interviewer / HR Head

- Login/logout
- Reset password
- View profile
- Edit profile
- Access role-specific dashboard

### Authentication

- Use JWT authentication.
- Use email as login identifier.
- Use role-based permissions.
- Protect every role-specific endpoint.

## 4. Organization and Team Setup Requirements

HR Department Head can:

- Create organization account
- Update organization details
- Deactivate organization account
- Create recruiter accounts
- Create interviewer accounts
- Bulk import recruiter/interviewer accounts by CSV first
- Search recruiter/interviewer accounts
- Deactivate recruiter/interviewer accounts

Applicants do not belong to an organization.

Recruiters, interviewers, and HR heads belong to an organization.

## 5. Job Posting and Requirement Configuration Requirements

Recruiter can:

- Create job posting
- Edit job posting
- Delete job posting
- Duplicate job posting
- Configure job requirements
- Assign weight to each job requirement
- Create job-specific interview evaluation form
- Add evaluation criteria

Applicant can:

- View open job postings
- Search/filter job postings
- View job posting details
- Save job posting
- Unsave job posting
- View saved job postings

## 6. Job Application Requirements

Applicant can:

- Apply for open job posting
- Withdraw application if still allowed
- View own applications
- View application status history

Recruiter can:

- View applications for own job postings
- View application details
- View candidate profile
- View status history

HR head can:

- View organization-level application information if needed

Every application status change must be recorded in stage history.

## 7. AI Resume Screening Requirements

The system should support AI-assisted resume screening.

Required score components:

- Semantic score
- Skill score
- Experience score
- Education score
- Final score

Formula:

```text
final_score = 0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score
```

The system should store:

- Extracted resume text
- Extracted skills
- Extracted experience
- Extracted education
- Score breakdown
- Explanation JSON

The system should rank candidates by final score.

AI must not automatically make final rejection/hiring decisions.

Low scoring candidates should be marked as `screened_not_qualified`, not permanently rejected.

## 8. Candidate Ranking and Shortlisting Requirements

Recruiter can:

- View ranked list of candidates for a job posting
- View candidate profile
- View AI score breakdown
- Add recruiter remark
- Shortlist candidate
- Assign candidate to interviewer
- Reject candidate manually

Interviewer should be able to see recruiter remarks for assigned candidates.

## 9. Interview Management Requirements

Recruiter can:

- Assign interviewer to shortlisted candidate

Interviewer can:

- View assigned candidates
- View candidate profile
- Send interview invitation
- Propose interview date/time
- Specify interview mode
- Specify meeting link or physical location
- Track invitation response status
- View upcoming/completed interviews

Applicant can:

- View received interview invitations
- Accept invitation
- Decline invitation with reason
- View upcoming/completed interviews
- View interview details

For early development, store calendar data locally.

Do not require Google Calendar OAuth at the beginning.

## 10. Interview Evaluation Requirements

Interviewer can:

- Upload interview audio recording
- Generate transcript
- Generate AI summary
- Edit AI summary
- Fill in evaluation form
- Submit evaluation

Recruiter can:

- View interview transcript
- View AI summary
- View interviewer evaluation answers
- Use these items to support hiring decision

## 11. Hiring Decision and Approval Requirements

Recruiter can:

- Submit final decision: hire or reject
- Provide justification
- Submit decision to HR head
- View HR head approval result
- Send job offer after approval

HR Department Head can:

- View pending hiring decisions
- Approve hiring decision with justification
- Reject hiring decision with justification

Applicant can:

- View job offer
- Accept job offer
- Decline job offer

Every status change must be recorded.

## 12. Notification Requirements

The system should support in-app notifications first.

Notification events include:

- Application status update
- Interview assignment
- Interview invitation
- Invitation response
- Upcoming interview reminder
- Evaluation submitted
- Hiring decision submitted
- Hiring decision approved/rejected
- Job offer sent
- Offer accepted/declined
- Subscription/billing reminder

Firebase push notification can be added later.

## 13. Analytics and Reporting Requirements

Recruiter analytics:

- Total job postings
- Total applications
- Candidate counts by status
- Shortlisted count
- Rejected count
- Hired count
- Average time-to-hire
- Candidate funnel

Interviewer analytics:

- Assigned interviews
- Completed interviews
- Evaluation submission count
- Average evaluation score

HR head analytics:

- Organization-level application counts
- Hiring success rate
- Rejection rate
- Candidate dropout rate
- Offer acceptance rate
- Recruiter performance
- Interviewer performance

PDF export should be supported later using ReportLab.

## 14. Subscription and Billing Requirements

HR head can:

- View subscription plans
- Select plan
- Make demo payment
- Upgrade/downgrade plan
- View invoices/payment history

Subscription plan should affect:

- Maximum open job postings

Use demo payment first.

Add real Stripe/PayPal/FPX only if time remains.

## 15. Non-Functional Requirements

The system should be:

- Secure
- Role-protected
- Organization-isolated
- Maintainable
- Scalable enough for FYP demonstration
- Easy to use
- Responsive enough for normal local development
- Clear in error handling

Sensitive data should be protected:

- Resume files
- Interview recordings
- Contact information
- Organization information
- Employment information

## 16. Development Priority

Highest priority:

1. Authentication
2. Organization setup
3. Job posting
4. Application workflow
5. AI resume screening
6. Candidate ranking
7. Interview management
8. Interview evaluation
9. Hiring approval

Medium priority:

1. Notifications
2. Analytics
3. PDF export
4. Billing demo

Lower priority / optional:

1. Real SendGrid
2. Real Firebase push notification
3. Real Google Calendar sync
4. Real payment gateway
5. Real LinkedIn OAuth
6. Real S3 storage
7. Celery/Redis background tasks
