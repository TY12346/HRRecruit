import 'package:dio/dio.dart';

import '../api/api_client.dart';
import '../models/applicant_profile.dart';
import '../models/auth_result.dart';

class ApplicantAuthService {
  const ApplicantAuthService(this._apiClient);

  final ApiClient _apiClient;

  Future<AuthResult> register({
    required String fullName,
    required String email,
    required String phoneNumber,
    required String password,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/register-applicant/',
      data: {
        'full_name': fullName,
        'email': email,
        'phone_number': phoneNumber,
        'password': password,
      },
    );

    return AuthResult.fromJson(response.data!);
  }

  Future<AuthResult> login({
    required String email,
    required String password,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/login/',
      data: {
        'email': email,
        'password': password,
      },
    );

    return AuthResult.fromJson(response.data!);
  }

  Future<void> logout({required String refreshToken}) async {
    await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/logout/',
      data: {'refresh': refreshToken},
    );
  }

  Future<ApplicantProfile> getProfile() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>('auth/profile/');
    return ApplicantProfile.fromJson(response.data!);
  }

  Future<ApplicantProfile> updateProfile({
    required String fullName,
    required String phoneNumber,
    required String linkedinUrl,
    required String personalSummary,
  }) async {
    final response = await _apiClient.dio.patch<Map<String, dynamic>>(
      'auth/profile/',
      data: {
        'full_name': fullName,
        'phone_number': phoneNumber,
        'linkedin_url': linkedinUrl,
        'personal_summary': personalSummary,
      },
    );

    final data = response.data!;
    return ApplicantProfile.fromJson(data['user'] as Map<String, dynamic>);
  }

  Future<String?> uploadResume({
    required String path,
    required String fileName,
  }) async {
    final formData = FormData.fromMap({
      'resume_file': await MultipartFile.fromFile(path, filename: fileName),
    });
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/resume/upload/',
      data: formData,
      options: Options(contentType: 'multipart/form-data'),
    );

    return response.data?['resume_file'] as String?;
  }
}
