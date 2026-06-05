import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

String readableApiError(Object error) {
  if (error is DioException) {
    if (_isConnectionProblem(error)) {
      return 'Could not reach the HRRecruit API. If you are using a '
          'physical phone, tap API settings and use '
          'http://YOUR_COMPUTER_LAN_IP:8000/api/. Also run Django with '
          'python manage.py runserver 0.0.0.0:8000.';
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

void showErrorSnackBar(BuildContext context, Object error) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(readableApiError(error))),
  );
}
