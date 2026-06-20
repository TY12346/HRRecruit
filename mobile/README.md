# HRRecruit Mobile

Flutter mobile app for HRRecruit job applicants.

## Setup

```bash
cd mobile
flutter pub get
flutter run
```

## Backend API URL

The app now chooses the safest local default for the current Flutter target:

- Android emulator: `http://10.0.2.2:8000/api/`
- iOS simulator, desktop, or Flutter web: `http://localhost:8000/api/`

`10.0.2.2` is only valid for the Android emulator.

When running on a physical phone or tablet:

1. Connect the phone and development computer to the same Wi-Fi network.
2. Start Django so it listens on your LAN interface:

   ```bash
   cd backend
   python manage.py runserver 0.0.0.0:8000
   ```

3. Make sure `DJANGO_ALLOWED_HOSTS` includes your computer LAN IP, for example
   `192.168.1.10`.
4. In the Flutter login or register screen, tap **API settings** and set:

   ```text
   http://YOUR_COMPUTER_LAN_IP:8000/api/
   ```

   If you omit `:8000`, Android will try port `80` and the app will show the
   API-unreachable message even though `:8000` works in a browser.

You can also pass the URL at launch time:

```bash
flutter run --dart-define=HRRECRUIT_API_BASE_URL=http://YOUR_COMPUTER_LAN_IP:8000/api/
```


### Windows firewall note

If the app still says the API is unreachable after setting the LAN IP, allow
Python/Django through Windows Firewall or temporarily allow inbound TCP traffic
on port `8000` for your private Wi-Fi network. A physical phone cannot reach a
Django server that is bound only to `127.0.0.1` or blocked by the firewall.


### Android cleartext HTTP note

The local backend URL uses plain HTTP, not HTTPS. Android apps can block
cleartext HTTP even when the same URL works in Chrome or another browser. The
tracked Android manifest enables cleartext traffic for local FYP development via
`android:usesCleartextTraffic="true"` and `@xml/network_security_config`.

If you already have an untracked/generated `android/` folder locally, make sure
`mobile/android/app/src/main/AndroidManifest.xml` contains the same
`uses-permission`, `usesCleartextTraffic`, and `networkSecurityConfig` entries.

## LinkedIn PDF profile import
The applicant profile screen imports LinkedIn data from a PDF copy of the
applicant's LinkedIn profile. This flow does not use LinkedIn OAuth and does not
ask the applicant for a LinkedIn Client ID, Client Secret, or LinkedIn password.

Applicant flow:

1. Open your LinkedIn profile in LinkedIn.
2. Save or download the profile as a PDF.
3. In HRRecruit mobile, open **Profile** and tap **Import LinkedIn PDF**.
4. Select the LinkedIn profile PDF.
5. HRRecruit uploads the PDF to the API, extracts text from the PDF, extracts
   profile details such as name, headline, skills, experience, education, and
   certifications, then fills the candidate profile automatically.

The applicant profile screen imports LinkedIn data from a PDF copy of the
applicant's LinkedIn profile. This flow does not use LinkedIn OAuth and does not
ask the applicant for a LinkedIn Client ID, Client Secret, or LinkedIn password.

Applicant flow:

1. Open your LinkedIn profile in LinkedIn.
2. Save or download the profile as a PDF.
3. In HRRecruit mobile, open **Profile** and tap **Import LinkedIn PDF**.
4. Select the LinkedIn profile PDF.
5. HRRecruit uploads the PDF to the API, extracts text from the PDF, extracts
   profile details such as name, headline, skills, experience, education, and
   certifications, then fills the candidate profile automatically.

The backend uses deterministic local PDF/text extraction for this early FYP
implementation. No real LinkedIn API or external AI API call is required.
