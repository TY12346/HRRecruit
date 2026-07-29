import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hrrecruit_mobile/screens/auth_form_helpers.dart';

void main() {
  group('readableApiError', () {
    test('replaces the invalid JWT detail with an expired-session message', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/api/applicant/profile/'),
        response: Response<Map<String, dynamic>>(
          requestOptions: RequestOptions(path: '/api/applicant/profile/'),
          statusCode: 401,
          data: const {
            'detail': 'Given token not valid',
            'code': 'token_not_valid',
          },
        ),
      );

      expect(
        readableApiError(error),
        'Login session expired. Please login again.',
      );
    });

    test('continues to display unrelated API details', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/api/login/'),
        response: Response<Map<String, dynamic>>(
          requestOptions: RequestOptions(path: '/api/login/'),
          statusCode: 401,
          data: const {'detail': 'Invalid email or password.'},
        ),
      );

      expect(readableApiError(error), 'Invalid email or password.');
    });
  });
}
