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
    final messaging = await _messagingOrNull();
    if (messaging == null) return;

    await messaging.requestPermission();
    final token = await messaging.getToken();
    if (token != null && token.isNotEmpty) {
      await _registerToken(token);
    }

    if (!_tokenRefreshListenerAttached) {
      _tokenRefreshListenerAttached = true;
      messaging.onTokenRefresh.listen((newToken) {
        if (newToken.isNotEmpty) {
          _registerToken(newToken);
        }
      });
    }
  }

  Future<FirebaseMessaging?> _messagingOrNull() async {
    try {
      if (!_initialized) {
        await Firebase.initializeApp();
        _initialized = true;
      }
      return FirebaseMessaging.instance;
    } catch (error) {
      debugPrint('Firebase Messaging is not configured: $error');
      return null;
    }
  }

  Future<void> _registerToken(String token) async {
    try {
      await _apiClient.dio.post<Map<String, dynamic>>(
        'notifications/push-devices/',
        data: {
          'registration_token': token,
          'platform': _platformName(),
          'device_id': '',
          'app_version': '0.1.0',
        },
      );
    } catch (error) {
      debugPrint('Unable to register FCM token with HRRecruit API: $error');
    }
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
