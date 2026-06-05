import 'package:dio/dio.dart';

import '../services/token_storage.dart';

class ApiClient {
  ApiClient({
    required TokenStorage tokenStorage,
    String baseUrl = defaultBaseUrl,
  })  : _tokenStorage = tokenStorage,
        dio = Dio(
          BaseOptions(
            baseUrl: baseUrl,
            connectTimeout: const Duration(seconds: 8),
            sendTimeout: const Duration(seconds: 8),
            receiveTimeout: const Duration(seconds: 8),
            headers: const {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
          ),
        ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final accessToken = await _tokenStorage.readAccessToken();

          if (accessToken != null && accessToken.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $accessToken';
          }

          handler.next(options);
        },
      ),
    );
  }

  static const defaultBaseUrl = String.fromEnvironment(
    'HRRECRUIT_API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/',
  );

  final TokenStorage _tokenStorage;
  final Dio dio;
}
