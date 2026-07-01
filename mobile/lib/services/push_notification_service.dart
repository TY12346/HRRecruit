import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../api/api_client.dart';

class PushNotificationService {
  PushNotificationService(this._apiClient);

  final ApiClient _apiClient;
  bool _initialized = false;
  bool _tokenRefreshListenerAttached = false;

  Future<void> registerDevice() async {
    final messaging = await _messaging();

    final settings = await messaging.requestPermission();
    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      throw StateError('FCM notification permission was denied.');
    }
    final token = await messaging.getToken();
    if (token == null || token.isEmpty) {
      throw StateError(
        'Firebase Messaging did not return an FCM registration token.',
      );
    }
    await _registerToken(token);

    if (!_tokenRefreshListenerAttached) {
      _tokenRefreshListenerAttached = true;
      messaging.onTokenRefresh.listen((newToken) async {
        if (newToken.isEmpty) {
          throw StateError(
            'Firebase Messaging returned an empty refreshed FCM token.',
          );
        }
        await _registerToken(newToken);
      });
    }
  }

  Future<FirebaseMessaging> _messaging() async {
    if (!_initialized) {
      await Firebase.initializeApp();
      _initialized = true;
    }
    return FirebaseMessaging.instance;
  }

  Future<void> _registerToken(String token) async {
    await _apiClient.dio.post<Map<String, dynamic>>(
      'notifications/push-devices/',
      data: {
        'registration_token': token,
        'platform': _platformName(),
        'device_id': '',
        'app_version': '0.1.0',
      },
    );
  }

  String _platformName() {
    if (kIsWeb) return 'web';
    return switch (defaultTargetPlatform) {
      TargetPlatform.iOS || TargetPlatform.macOS => 'ios',
      TargetPlatform.android || TargetPlatform.fuchsia => 'android',
      TargetPlatform.linux || TargetPlatform.windows => 'web',
    };
  }
}
