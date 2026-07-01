import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  TokenStorage({FlutterSecureStorage? secureStorage})
      : _secureStorage = secureStorage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'hrrecruit_access_token';
  static const _refreshTokenKey = 'hrrecruit_refresh_token';
  static const _apiBaseUrlKey = 'hrrecruit_api_base_url';

  final FlutterSecureStorage _secureStorage;

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _secureStorage.write(key: _accessTokenKey, value: accessToken);
    await _secureStorage.write(key: _refreshTokenKey, value: refreshToken);
  }

  Future<String?> readAccessToken() {
    return _secureStorage.read(key: _accessTokenKey);
  }

  Future<String?> readRefreshToken() {
    return _secureStorage.read(key: _refreshTokenKey);
  }

  Future<void> saveApiBaseUrl(String apiBaseUrl) {
    return _secureStorage.write(key: _apiBaseUrlKey, value: apiBaseUrl);
  }

  Future<String?> readApiBaseUrl() {
    return _secureStorage.read(key: _apiBaseUrlKey);
  }

  Future<void> clearApiBaseUrl() {
    return _secureStorage.delete(key: _apiBaseUrlKey);
  }

  Future<void> clearTokens() async {
    await Future.wait([
      _secureStorage.delete(key: _accessTokenKey),
      _secureStorage.delete(key: _refreshTokenKey),
    ]);
  }
}
