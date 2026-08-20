# Migration Recovery

## `flush` fails or `django-admin sqlflush` says settings are not configured

Run database commands through this project's `manage.py`, from the `backend`
directory. Unlike a bare `django-admin` invocation, `manage.py` configures
`DJANGO_SETTINGS_MODULE=config.settings` for this project:

```powershell
cd C:\FYP\hrrecruit\backend
python manage.py sqlflush
```

The `django-admin sqlflush` error about `DATABASES` not being configured is a
separate command-invocation problem; it does not reveal why the earlier flush
failed. Do not use bare `django-admin` for this diagnosis. In particular,
`django-admin sqlflush --settings=config.settings` is not a reliable substitute:
the `sqlflush` command accesses the configured database connections while it is
building its argument parser, and that can happen before the command-line
settings option takes effect. On Windows it can therefore fail with either
`Requested setting DATABASES, but settings are not configured` or
`ModuleNotFoundError: No module named 'config'`. The project's `manage.py`
establishes the settings module before Django constructs the command, so use
`python manage.py sqlflush` instead.

Use the following checks to distinguish configuration, migration, and flush
problems. These commands do not delete data:

```powershell
python manage.py check --database default
python manage.py showmigrations
python manage.py migrate --plan
python manage.py sqlflush
```

- If the database check cannot connect, verify that PostgreSQL is running and
  that `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and
  `POSTGRES_PORT` in `backend/.env` identify the intended database.
- If `showmigrations` contains any `[ ]` entry, stop troubleshooting `flush` and
  apply that migration first. For example, an output containing
  `[ ] 0020_remove_legacy_evaluation_importance_level` means the local schema is
  one migration behind the checked-out code. Apply it before retrying the flush:

  ```powershell
  python manage.py migrate
  python manage.py sqlflush
  python manage.py flush
  ```

  Confirm that `migrate` completes successfully and that a subsequent
  `showmigrations` has no `[ ]` entries. Do not run `flush` between detecting an
  unapplied migration and applying it.

- If `sqlflush` prints valid SQL but `flush` still reports only the generic
  `CommandError`, run the generated SQL through PostgreSQL to expose the database
  error that Django's `flush` command hides:

  ```powershell
  python manage.py sqlflush | python manage.py dbshell
  ```

  This is destructive when it succeeds, just like `flush`. A PostgreSQL error
  such as `cannot truncate a table referenced in a foreign key constraint`
  identifies a stale or non-Django table that references one of the managed
  tables. Record the constraint and table names from that error before choosing
  a recovery path.

  For a disposable local database that is intentionally being emptied, rerun
  the SQL with PostgreSQL's explicit `CASCADE` option, then recreate Django's
  post-migration records:

  ```powershell
  python manage.py sqlflush |
    ForEach-Object { $_ -replace 'RESTART IDENTITY;', 'RESTART IDENTITY CASCADE;' } |
    python manage.py dbshell
  python manage.py migrate
  ```

  `CASCADE` can also empty tables not listed by `sqlflush` when foreign keys link
  them to Django tables. Use it only after confirming that every table in this
  local database is safe to empty. On a shared or non-disposable database,
  repair or remove the unexpected foreign-key/table instead of using `CASCADE`.

Do not delete migration files or remove individual rows from
`django_migrations` to repair a flush. If the goal is a completely fresh local
development database and no data must be retained, recreate the database and
then rebuild its schema instead:

```powershell
# Run these in psql while connected to a different database, such as postgres.
DROP DATABASE hrrecruit_db;
CREATE DATABASE hrrecruit_db;

# Then return to the backend directory.
python manage.py migrate
```

Only use the drop-and-create path for a local database whose contents are safe
to destroy. Database ownership or project-specific PostgreSQL privileges may
need to be included in the `CREATE DATABASE` statement.

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
