# HRRecruit Mobile

Flutter mobile app for HRRecruit job applicants.

## Setup

```bash
cd mobile
flutter pub get
flutter run
```

## Backend API URL

The mobile app defaults to `http://10.0.2.2:8000/api/`, which is only valid
for the Android emulator.

When running on a physical phone:

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

You can also pass the URL at launch time:

```bash
flutter run --dart-define=HRRECRUIT_API_BASE_URL=http://YOUR_COMPUTER_LAN_IP:8000/api/
```


### Windows firewall note

If the app still says the API is unreachable after setting the LAN IP, allow
Python/Django through Windows Firewall or temporarily allow inbound TCP traffic
on port `8000` for your private Wi-Fi network. A physical phone cannot reach a
Django server that is bound only to `127.0.0.1` or blocked by the firewall.
