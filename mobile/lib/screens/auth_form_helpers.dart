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
      return 'Could not reach the HRRecruit API.$currentUrl\n\n'
          'Use http://10.0.2.2:8000/api/ only for the Android emulator. '
          'Use http://localhost:8000/api/ for iOS simulator, desktop, or web. '
          'For a physical phone, tap API settings and use '
          'http://YOUR_COMPUTER_LAN_IP:8000/api/. Do not omit :8000.\n\n'
          'Also check that Django is running with '
          'python manage.py runserver 0.0.0.0:8000, that Windows Firewall '
          'allows port 8000, DJANGO_ALLOWED_HOSTS includes your LAN IP, '
          'and Android cleartext HTTP is enabled for local development.';
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

bool _isConnectionProblem(DioException error) {
  return error.type == DioExceptionType.connectionTimeout ||
      error.type == DioExceptionType.sendTimeout ||
      error.type == DioExceptionType.receiveTimeout ||
      error.type == DioExceptionType.connectionError ||
      error.response == null;
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
