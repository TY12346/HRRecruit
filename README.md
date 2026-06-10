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

## FYP demo seed data

For a complete fake demo dataset, run the demo seed command after migrations:

```bash
cd backend
python manage.py migrate
python manage.py seed_demo_data
```

The command creates safe fake accounts for the HR head, recruiter, interviewer, and applicant; a demo organization; two open jobs; a Software Engineer application with mock AI screening scores; interview transcript/summary/evaluation records; hiring approval and accepted offer records; notifications; and demo-mode subscription billing records. It is idempotent and does not delete or reset existing data.

Default demo credentials:

| Role | Email | Password |
| --- | --- | --- |
| HR Head | demo.hrhead@example.com | DemoPass123! |
| Recruiter | demo.recruiter@example.com | DemoPass123! |
| Interviewer | demo.interviewer@example.com | DemoPass123! |
| Applicant | demo.applicant@example.com | DemoPass123! |

See [DEMO_GUIDE.md](DEMO_GUIDE.md) for the full demo setup order, expected records, workflow, and external integration notes. All seeded demo data is fake, and external integrations use local/mock/demo mode unless explicitly configured.

## Demo HR-head bootstrap

If you only need the first HR Department Head account instead of the full dataset, bootstrap it with:

```bash
cd backend
python manage.py bootstrap_demo_hr_head --email hr-head.demo@hrrecruit.test --password DemoPass123!
```
