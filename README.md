# HRRecruit

HRRecruit is a Final Year Project (FYP) system for an AI-powered recruitment management SaaS.

## Main Platforms

- **Backend:** Django REST Framework
- **Database:** PostgreSQL
- **Web Portal:** React.js for Recruiter, Interviewer, and HR Department Head
- **Mobile App:** Flutter for Job Applicant
- **AI Features:** Resume screening, candidate ranking, interview transcription, and interview summary generation

## Main User Roles

1. Job Applicant
2. Recruiter
3. Interviewer
4. HR Department Head

## Development Strategy

This project must be developed incrementally.

Recommended order:

1. Backend foundation
2. Custom user model
3. Authentication and role-based access control
4. Organization and team setup
5. Job posting and requirement configuration
6. Applicant profile, resume upload, job discovery, and saved jobs
7. Job application workflow
8. AI resume screening
9. Candidate ranking and shortlisting
10. Interview management
11. Interview evaluation and AI summary
12. Hiring decision and HR approval workflow
13. In-app notifications
14. Analytics and PDF reporting
15. Subscription and demo billing
16. Backend testing
17. React web portal
18. Flutter applicant mobile app
19. Optional real integrations

## Important Note

The written FYP requirements are the main source of truth.

Do **not** follow Chapter 4 ERD, UML, use case, sequence, or process diagrams because they are considered incorrect.

Only Chapter 4 UI design screens may be used as visual reference.

## Demo HR-head bootstrap

For the FYP demo, bootstrap the first HR Department Head account with a management command instead of using a public HR-head registration page:

```bash
cd backend
python manage.py bootstrap_demo_hr_head --email hr-head.demo@hrrecruit.test --password DemoPass123!
```

Then log in to the web portal with that HR-head account, create the demo organization, and add recruiter/interviewer team members through the normal organization flow. A later seed-data prompt can extend this into a complete one-command demo dataset with jobs, candidates, interviews, evaluations, offers, and analytics-ready hired applications.
