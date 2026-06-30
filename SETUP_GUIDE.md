# HRRecruit Setup Guide

This guide explains how to set up HRRecruit locally for development, examiner review, and FYP demonstration.

## Prerequisites

Install the following tools before starting:

- Python 3.11
- PostgreSQL
- Node.js and npm
- Flutter SDK
- Git

Recommended local ports:

- Django backend: `http://localhost:8000`
- React web portal: `http://localhost:5173`
- PostgreSQL: `127.0.0.1:5432`

## PostgreSQL Setup Assumptions

The backend is configured to use PostgreSQL from the start. Unless overridden in `backend/.env`, the expected values are:

| Setting | Default / Variable |
| --- | --- |
| Database name | `POSTGRES_DB=hrrecruit_db` |
| Username | `POSTGRES_USER=postgres` |
| Password | `POSTGRES_PASSWORD=` |
| Host | `POSTGRES_HOST=127.0.0.1` |
| Port | `POSTGRES_PORT=5432` |

Create the database before running migrations. Example using `psql`:

```bash
createdb hrrecruit_db
```

If your PostgreSQL user requires a password, set `POSTGRES_PASSWORD` in `backend/.env`.

## Backend Setup

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

### Configure backend `.env`

Create `backend/.env` if it does not exist:

```bash
cp .env.example .env  # only if you have created an example file locally
```

If there is no backend `.env.example`, create `backend/.env` manually:

```env
DJANGO_SECRET_KEY=replace-this-for-local-dev
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

POSTGRES_DB=hrrecruit_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# External integrations. AI integrations are strict: missing credentials cause clear API errors.
SENDGRID_API_KEY=
DEFAULT_FROM_EMAIL=no-reply@hrrecruit.local

FIREBASE_PUSH_ENABLED=False
FIREBASE_PROJECT_ID=
FIREBASE_CREDENTIALS_PATH=
FIREBASE_CREDENTIALS_JSON=
FIREBASE_USE_APPLICATION_DEFAULT_CREDENTIALS=False

GOOGLE_CALENDAR_ENABLED=False
GOOGLE_CALENDAR_CLIENT_ID=
GOOGLE_CALENDAR_CLIENT_SECRET=
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:5173/recruiter/calendar/google/callback
GOOGLE_CALENDAR_DEFAULT_DURATION_MINUTES=60
OPENAI_API_KEY=
TRANSCRIPTION_MODEL=whisper-1
USE_REAL_TRANSCRIPTION=True
SUMMARY_MODEL=gpt-4o-mini
USE_REAL_SUMMARY=True
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_CHECKOUT_SUCCESS_URL=http://localhost:5173/billing/success
STRIPE_CHECKOUT_CANCEL_URL=http://localhost:5173/billing/cancel
STRIPE_CURRENCY=MYR
```

### Run migrations

```bash
python manage.py migrate
```

### Create a superuser if needed

A Django admin user is optional for the demo but useful for inspecting data:

```bash
python manage.py createsuperuser
```

### Seed demo data

For the full FYP demo dataset:

```bash
python manage.py seed_demo_data
```

The command is designed to be safe to run multiple times. It creates/updates fake demo users, organization, jobs, application, AI screening data, interview data, hiring approval data, notifications, and billing demo records.

If you only need an initial HR-head account instead of the full dataset, the repository also includes:

```bash
python manage.py bootstrap_demo_hr_head --email hr-head.demo@hrrecruit.test --password DemoPass123!
```

### Run the backend server

```bash
python manage.py runserver
```

For physical mobile-device testing on the same Wi-Fi network:

```bash
python manage.py runserver 0.0.0.0:8000
```

Make sure `DJANGO_ALLOWED_HOSTS` includes your computer's LAN IP when using a physical phone.

## React Web Portal Setup

From the repository root:

```bash
cd web
npm install
```

For reproducible installs when `package-lock.json` is present, you may use:

```bash
npm ci
```

Create a web `.env` file:

```bash
cp .env.example .env
```

Set the backend API base URL:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Run the web portal:

```bash
npm run dev
```

Build the web portal:

```bash
npm run build
```

Optional lint check:

```bash
npm run lint
```

## Flutter Applicant Mobile App Setup

From the repository root:

```bash
cd mobile
flutter pub get
flutter analyze
flutter run
```

The mobile app defaults to the Android emulator backend URL:

```text
http://10.0.2.2:8000/api/
```

For a physical phone, start Django on `0.0.0.0:8000`, ensure firewall access, add your LAN IP to `DJANGO_ALLOWED_HOSTS`, and configure the mobile app's API setting to:

```text
http://YOUR_COMPUTER_LAN_IP:8000/api/
```

You can also pass the API URL at launch:

```bash
flutter run --dart-define=HRRECRUIT_API_BASE_URL=http://YOUR_COMPUTER_LAN_IP:8000/api/
```

## Demo Data Accounts

After running `python manage.py seed_demo_data`, all seeded demo users use this password by default:

```text
DemoPass123!
```

| Role | Email |
| --- | --- |
| HR Head | demo.hrhead@example.com |
| Recruiter | demo.recruiter@example.com |
| Interviewer | demo.interviewer@example.com |
| Applicant | demo.applicant@example.com |

To set a different password for all demo users:

```bash
python manage.py seed_demo_data --password 'AnotherValidPass123!'
```

To refresh demo data without changing existing demo passwords:

```bash
python manage.py seed_demo_data --no-update-password
```

## Common Troubleshooting

### PostgreSQL connection refused

- Confirm PostgreSQL is installed and running.
- Confirm the database exists.
- Confirm `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in `backend/.env` match your local PostgreSQL configuration.
- Try connecting manually with `psql` before running Django migrations.

### Missing npm dependencies such as Vite

- Run `npm install` in the `web/` directory.
- If a lockfile exists and dependencies are inconsistent, try removing `node_modules` and running `npm ci`.
- Confirm you are using a recent Node.js/npm version.

### Flutter analyzer or run issues

- Run `flutter doctor` and resolve missing platform tooling.
- Run `flutter pub get` before `flutter analyze` or `flutter run`.
- For Android emulator networking, use `http://10.0.2.2:8000/api/`.
- For physical phones, use the computer LAN IP and allow inbound traffic on port `8000`.

### Firebase mobile push notification setup

- Create a Firebase project and Android app for the Flutter package.
- Download the Firebase Admin service account JSON file.
- Set `FIREBASE_PUSH_ENABLED=True`, `FIREBASE_PROJECT_ID`, and `FIREBASE_CREDENTIALS_PATH` to the JSON file path.
- The mobile app can register its FCM token through `POST /api/notifications/push-devices/`.

### Google Calendar API interview sync setup

- Create a Google Cloud OAuth client and enable the Google Calendar API.
- Set `GOOGLE_CALENDAR_ENABLED=True`, `GOOGLE_CALENDAR_CLIENT_ID`, `GOOGLE_CALENDAR_CLIENT_SECRET`, and `GOOGLE_CALENDAR_REDIRECT_URI`.
- Add the same redirect URI to the Google Cloud OAuth client. For local React development, use `http://localhost:5173/recruiter/calendar/google/callback`.
- Recruiters can connect Google Calendar from the interview assignment page; booked interview slots then create/update real Google Calendar events with attendees and Google Meet links when needed.

### Missing AI/payment/email/calendar keys

- AI features are strict: resume semantic matching, trained resume matching, real transcription, and real summary generation return clear errors when their required model/dependency/credential is missing.
- Configure `OPENAI_API_KEY`, `USE_REAL_TRANSCRIPTION=True`, `USE_REAL_SUMMARY=True`, and train the resume matching model before demoing AI flows.
- Non-AI integrations still require valid credentials, network access, callback URLs, and security configuration before enabling production behavior.
