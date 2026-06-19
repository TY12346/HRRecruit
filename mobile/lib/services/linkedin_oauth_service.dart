import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';

class LinkedInImportedProfile {
  const LinkedInImportedProfile({
    required this.profileUrl,
    required this.summary,
  });

  final String profileUrl;
  final String summary;
}

class LinkedInOAuthService {
  LinkedInOAuthService({Dio? dio}) : _dio = dio ?? Dio();

  static const clientId = String.fromEnvironment('LINKEDIN_CLIENT_ID');
  static const redirectUri = String.fromEnvironment(
    'LINKEDIN_REDIRECT_URI',
    defaultValue: 'hrrecruit://linkedin-oauth',
  );
  static const callbackUrlScheme = String.fromEnvironment(
    'LINKEDIN_CALLBACK_SCHEME',
    defaultValue: 'hrrecruit',
  );

  static final _authorizationEndpoint = Uri.parse(
    'https://www.linkedin.com/oauth/v2/authorization',
  );
  static final _tokenEndpoint = Uri.parse(
    'https://www.linkedin.com/oauth/v2/accessToken',
  );
  static final _userInfoEndpoint = Uri.parse(
    'https://api.linkedin.com/v2/userinfo',
  );

  final Dio _dio;

  Future<LinkedInImportedProfile> importProfile() async {
    if (clientId.isEmpty) {
      throw Exception(
        'LinkedIn OAuth is not configured. Build the app with '
        '--dart-define=LINKEDIN_CLIENT_ID=your_linkedin_client_id.',
      );
    }

    final state = _randomUrlSafeString(32);
    final codeVerifier = _randomUrlSafeString(64);
    final codeChallenge = _pkceChallenge(codeVerifier);
    final authorizationUrl = _authorizationEndpoint.replace(
      queryParameters: {
        'response_type': 'code',
        'client_id': clientId,
        'redirect_uri': redirectUri,
        'state': state,
        'scope': 'openid profile email',
        'code_challenge': codeChallenge,
        'code_challenge_method': 'S256',
      },
    );

    final callbackUrl = await FlutterWebAuth2.authenticate(
      url: authorizationUrl.toString(),
      callbackUrlScheme: callbackUrlScheme,
    );
    final callbackUri = Uri.parse(callbackUrl);

    final error = callbackUri.queryParameters['error'];
    if (error != null) {
      final description = callbackUri.queryParameters['error_description'];
      throw Exception(description == null ? error : '$error: $description');
    }

    if (callbackUri.queryParameters['state'] != state) {
      throw Exception('LinkedIn sign-in failed because the OAuth state did not match.');
    }

    final authorizationCode = callbackUri.queryParameters['code'];
    if (authorizationCode == null || authorizationCode.isEmpty) {
      throw Exception('LinkedIn did not return an authorization code.');
    }

    final tokenResponse = await _dio.post<Map<String, dynamic>>(
      _tokenEndpoint.toString(),
      data: {
        'grant_type': 'authorization_code',
        'code': authorizationCode,
        'redirect_uri': redirectUri,
        'client_id': clientId,
        'code_verifier': codeVerifier,
      },
      options: Options(contentType: Headers.formUrlEncodedContentType),
    );
    final accessToken = tokenResponse.data?['access_token'] as String?;
    if (accessToken == null || accessToken.isEmpty) {
      throw Exception('LinkedIn did not return an access token.');
    }

    final profileResponse = await _dio.get<Map<String, dynamic>>(
      _userInfoEndpoint.toString(),
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
    return _profileFromUserInfo(profileResponse.data ?? const {});
  }

  LinkedInImportedProfile _profileFromUserInfo(Map<String, dynamic> userInfo) {
    final name = (userInfo['name'] as String?)?.trim();
    final localizedFirstName = (userInfo['given_name'] as String?)?.trim();
    final localizedLastName = (userInfo['family_name'] as String?)?.trim();
    final email = (userInfo['email'] as String?)?.trim();
    final subject = (userInfo['sub'] as String?)?.trim();
    final displayName = name?.isNotEmpty == true
        ? name!
        : [localizedFirstName, localizedLastName]
            .where((part) => part != null && part.isNotEmpty)
            .join(' ');
    final profileUrl = subject == null || subject.isEmpty
        ? 'https://www.linkedin.com/'
        : 'https://www.linkedin.com/in/$subject';
    final importedParts = [
      if (displayName.isNotEmpty) displayName,
      if (email != null && email.isNotEmpty) email,
    ];
    final importedIdentity = importedParts.isEmpty
        ? 'LinkedIn member'
        : importedParts.join(' • ');

    return LinkedInImportedProfile(
      profileUrl: profileUrl,
      summary: '$importedIdentity imported their LinkedIn profile via OAuth 2.0 for recruiter review.',
    );
  }

  static String _randomUrlSafeString(int length) {
    final random = Random.secure();
    final values = List<int>.generate(length, (_) => random.nextInt(256));
    return base64UrlEncode(values).replaceAll('=', '');
  }

  static String _pkceChallenge(String codeVerifier) {
    final bytes = ascii.encode(codeVerifier);
    return base64UrlEncode(sha256.convert(bytes).bytes).replaceAll('=', '');
  }
}
