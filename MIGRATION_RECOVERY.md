# Migration Recovery

## Hiring decision terminology upgrade

The job-level hiring workflow is renamed by the forward-only migration
`hiring.0005_rename_job_hiring_models_to_decisions`.

Do **not** rename the historical migration file
`backend/apps/hiring/migrations/0003_jobhiringrecommendation_jobhiringrecommendationitem.py`.
Existing databases record this exact identifier in the `django_migrations` table,
and migration `0004_ensure_joboffer_applicant_response_note` must continue to
depend on that historical name.

If `python manage.py migrate` reports that `hiring.0004` is applied before
`hiring.0003_jobhiringdecision_jobhiringdecisionitem`, the checkout still has a
renamed historical migration dependency. Update the project so that:

```python
# backend/apps/hiring/migrations/0004_ensure_joboffer_applicant_response_note.py
dependencies = [
    ('hiring', '0003_jobhiringrecommendation_jobhiringrecommendationitem'),
]
```

Then run:

```powershell
cd backend
python manage.py migrate
```

Migration `0005` will apply the model and field renames without changing the
previously recorded migration history. Do not delete rows from `django_migrations`
or use `--fake` for this issue.
