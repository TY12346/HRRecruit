import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/api_client.dart';

String readableApiError(Object error, {String? apiBaseUrl}) {
  if (error is DioException) {
    if (_isConnectionProblem(error)) {
      final currentUrl = apiBaseUrl == null
          ? ''
          : '\nCurrent API URL: $apiBaseUrl';
      final details = _connectionErrorDetails(error);
      return 'Could not reach the HRRecruit API.$currentUrl\n\n'
          'Network detail: $details\n\n'
          'Use http://10.0.2.2:8000/api/ only for the Android emulator. '
          'Use http://localhost:8000/api/ for iOS simulator, desktop, or web. '
          'For a physical phone, tap API settings and use '
          'http://YOUR_COMPUTER_LAN_IP:8000/api/. Do not omit :8000.\n\n'
          'For a physical phone, also confirm the phone and computer are on '
          'the same Wi-Fi network and that mobile data, VPN, hotspot/client '
          'isolation, or guest Wi-Fi is not blocking access to the computer.\n\n'
          'Also check that Django is running with '
          'python manage.py runserver 0.0.0.0:8000, that Windows Firewall '
          'allows port 8000, DJANGO_ALLOWED_HOSTS includes your LAN IP, '
          'and Android cleartext HTTP is enabled for local development.';
    }

    if (_isTimeoutProblem(error)) {
      final currentUrl = apiBaseUrl == null
          ? ''
          : '\nCurrent API URL: $apiBaseUrl';
      return 'The HRRecruit API took too long to respond.$currentUrl\n\n'
          'Please wait a moment and try again. If this keeps happening, '
          'confirm Django is still running and increase local machine resources for the demo.';
    }

    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      if (data['detail'] != null) {
        return data['detail'].toString();
      }
      final messages = data.entries
          .map((entry) => '${entry.key}: ${_stringifyMessage(entry.value)}')
          .join('\n');
      if (messages.isNotEmpty) {
        return messages;
      }
    }
    if (data is String && data.isNotEmpty) {
      return data;
    }
  }

  final message = error.toString();
  if (message.startsWith('Exception: ')) {
    return message.replaceFirst('Exception: ', '');
  }

  return 'Something went wrong. Please try again.';
}

bool _isTimeoutProblem(DioException error) {
  return error.type == DioExceptionType.sendTimeout ||
      error.type == DioExceptionType.receiveTimeout;
}

bool _isConnectionProblem(DioException error) {
  return error.type == DioExceptionType.connectionTimeout ||
      error.type == DioExceptionType.connectionError ||
      error.response == null;
}

String _connectionErrorDetails(DioException error) {
  final details = <String>[
    error.type.toString().split('.').last,
    if (error.message != null && error.message!.isNotEmpty) error.message!,
    if (error.error != null) error.error.toString(),
  ];
  return details.toSet().join(' — ');
}

String _stringifyMessage(Object? value) {
  if (value is List) {
    return value.join(', ');
  }
  return value?.toString() ?? '';
}

Future<void> showErrorSnackBar(BuildContext context, Object error) async {
  String? apiBaseUrl;
  try {
    apiBaseUrl = await context.read<ApiClient>().currentBaseUrl();
  } catch (_) {
    apiBaseUrl = null;
  }

  if (!context.mounted) return;
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(readableApiError(error, apiBaseUrl: apiBaseUrl))),
  );
}
