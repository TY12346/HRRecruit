import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../services/token_storage.dart';

class ApiClient {
  ApiClient({
    required TokenStorage tokenStorage,
    String? baseUrl,
  })  : _tokenStorage = tokenStorage,
        dio = Dio(
          BaseOptions(
            baseUrl: normalizeBaseUrl(baseUrl ?? defaultBaseUrl),
            connectTimeout: const Duration(seconds: 15),
            sendTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 15),
            headers: const {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
          ),
        ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final configuredBaseUrl = await _tokenStorage.readApiBaseUrl();
          options.baseUrl = normalizeBaseUrl(
            _resolveConfiguredBaseUrl(configuredBaseUrl) ?? dio.options.baseUrl,
          );

          final accessToken = await _tokenStorage.readAccessToken();
          if (accessToken != null && accessToken.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $accessToken';
          }

          handler.next(options);
        },
        onError: (error, handler) {
          debugPrint(
            'HRRecruit API request failed: '
            '${error.requestOptions.method} '
            '${error.requestOptions.baseUrl}${error.requestOptions.path} '
            '${error.type} ${error.message}',
          );
          handler.next(error);
        },
      ),
    );
  }

  static const _configuredBaseUrl = String.fromEnvironment(
    'HRRECRUIT_API_BASE_URL',
  );

  static String get defaultBaseUrl {
    if (_configuredBaseUrl.isNotEmpty) {
      return _configuredBaseUrl;
    }

    if (kIsWeb) {
      return 'http://localhost:8000/api/';
    }

    return switch (defaultTargetPlatform) {
      TargetPlatform.iOS ||
      TargetPlatform.macOS ||
      TargetPlatform.linux ||
      TargetPlatform.windows =>
        'http://localhost:8000/api/',
      TargetPlatform.android || TargetPlatform.fuchsia =>
        'http://10.0.2.2:8000/api/',
    };
  }

  static String? _resolveConfiguredBaseUrl(String? storedBaseUrl) {
    if (storedBaseUrl == null || storedBaseUrl.trim().isEmpty) {
      return null;
    }

    final normalizedStoredBaseUrl = normalizeBaseUrl(storedBaseUrl);
    final normalizedDefaultBaseUrl = normalizeBaseUrl(defaultBaseUrl);
    final isLegacyAndroidEmulatorDefault =
        normalizedStoredBaseUrl == 'http://10.0.2.2:8000/api/';
    final defaultChangedForCurrentTarget =
        normalizedDefaultBaseUrl != normalizedStoredBaseUrl;

    if (isLegacyAndroidEmulatorDefault && defaultChangedForCurrentTarget) {
      return normalizedDefaultBaseUrl;
    }

    return normalizedStoredBaseUrl;
  }

  static String normalizeBaseUrl(String baseUrl) {
    final trimmed = baseUrl.trim();
    if (trimmed.isEmpty) {
      return defaultBaseUrl;
    }

    final uri = Uri.tryParse(trimmed);
    if (uri == null || uri.scheme.isEmpty || uri.host.isEmpty) {
      return trimmed.endsWith('/') ? trimmed : '$trimmed/';
    }

    final isLocalDevelopmentHost = uri.host == 'localhost' ||
        uri.host == '127.0.0.1' ||
        uri.host == '10.0.2.2' ||
        _isPrivateIpv4Address(uri.host);
    final shouldUseDjangoDevPort = uri.scheme == 'http' &&
        isLocalDevelopmentHost &&
        !uri.hasPort;
    final normalizedPath = _normalizeApiPath(uri.path);
    final normalizedUri = uri.replace(
      port: shouldUseDjangoDevPort
          ? 8000
          : (uri.hasPort ? uri.port : null),
      path: normalizedPath,
    );

    return normalizedUri.toString();
  }

  static String _normalizeApiPath(String path) {
    if (path.isEmpty || path == '/') {
      return '/api/';
    }
    return path.endsWith('/') ? path : '$path/';
  }

  static bool _isPrivateIpv4Address(String host) {
    final parts = host.split('.').map(int.tryParse).toList();
    if (parts.length != 4 || parts.any((part) => part == null)) {
      return false;
    }

    final first = parts[0]!;
    final second = parts[1]!;
    return first == 10 ||
        (first == 172 && second >= 16 && second <= 31) ||
        (first == 192 && second == 168);
  }

  Options longRunningRequestOptions() {
    return Options(
      sendTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 60),
    );
  }

  Future<void> updateBaseUrl(String baseUrl) async {
    final normalizedBaseUrl = normalizeBaseUrl(baseUrl);
    dio.options.baseUrl = normalizedBaseUrl;
    await _tokenStorage.saveApiBaseUrl(normalizedBaseUrl);
  }

  Future<String> currentBaseUrl() async {
    final storedBaseUrl = await _tokenStorage.readApiBaseUrl();
    return normalizeBaseUrl(
      _resolveConfiguredBaseUrl(storedBaseUrl) ?? dio.options.baseUrl,
    );
  }

  final TokenStorage _tokenStorage;
  final Dio dio;
}
