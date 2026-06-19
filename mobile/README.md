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

## LinkedIn OAuth profile import

The applicant profile screen can import LinkedIn identity data through LinkedIn
OAuth 2.0 / OpenID Connect. Create a LinkedIn Developer app, enable **Sign In
with LinkedIn using OpenID Connect**, and register this redirect URL in the
LinkedIn app settings:

```text
hrrecruit://linkedin-oauth
```

Configure the LinkedIn Client ID at build/run time. Applicants should never be asked to enter developer credentials such as a LinkedIn Client ID inside the app:

```bash
flutter run --dart-define=LINKEDIN_CLIENT_ID=YOUR_LINKEDIN_CLIENT_ID
```

If you change the redirect URI or scheme in LinkedIn Developer settings, pass the
matching Dart defines as well:

```bash
flutter run \
  --dart-define=LINKEDIN_CLIENT_ID=YOUR_LINKEDIN_CLIENT_ID \
  --dart-define=LINKEDIN_REDIRECT_URI=hrrecruit://linkedin-oauth \
  --dart-define=LINKEDIN_CALLBACK_SCHEME=hrrecruit
```

Do not put a LinkedIn Client Secret in the Flutter app. The mobile flow uses PKCE
with the public Client ID.

Applicant flow:

1. Tap **Import from LinkedIn**.
2. HRRecruit shows **Sign in to LinkedIn and allow access** and explains that
   LinkedIn OAuth 2.0 will open next.
3. Tap **Allow access**. HRRecruit adds LinkedIn's `prompt=login` OAuth
   parameter so LinkedIn prompts the applicant to enter or confirm their
   LinkedIn login credentials for the import. Sign in on LinkedIn with the
   LinkedIn account email and password, approve access, and return to
   HRRecruit.

HRRecruit never asks for or stores the user's LinkedIn password; credentials are
entered only on LinkedIn's OAuth screen.
