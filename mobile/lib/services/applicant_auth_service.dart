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

  Future<String?> requestPasswordReset({required String email}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/password-reset/request/',
      data: {'email': email, 'client_app': 'mobile'},
    );
    return response.data?['reset_code'] as String?;
  }

  Future<void> verifyPasswordResetOtp({
    required String email,
    required String otpCode,
  }) async {
    await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/password-reset/verify/',
      data: {
        'email': email,
        'client_app': 'mobile',
        'otp_code': otpCode,
      },
    );
  }

  Future<void> confirmPasswordReset({
    required String email,
    required String otpCode,
    required String newPassword,
  }) async {
    await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/password-reset/confirm/',
      data: {
        'email': email,
        'client_app': 'mobile',
        'otp_code': otpCode,
        'new_password': newPassword,
      },
    );
  }

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/password/change/',
      data: {
        'current_password': currentPassword,
        'new_password': newPassword,
      },
    );
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
    required List<ApplicantExperience> experiences,
    required List<ApplicantEducation> educations,
    required List<ApplicantSkill> skills,
  }) async {
    final response = await _apiClient.dio.patch<Map<String, dynamic>>(
      'auth/profile/',
      data: {
        'full_name': fullName,
        'phone_number': phoneNumber,
        'linkedin_url': linkedinUrl,
        'personal_summary': personalSummary,
        'experiences': experiences.map((item) => item.toJson()).toList(),
        'educations': educations.map((item) => item.toJson()).toList(),
        'skills': skills.map((item) => item.toJson()).toList(),
      },
    );

    final data = response.data!;
    return ApplicantProfile.fromJson(data['user'] as Map<String, dynamic>);
  }

  Future<ApplicantProfile> importLinkedInProfilePdf({
    required String path,
    required String fileName,
  }) async {
    final formData = FormData.fromMap({
      'linkedin_pdf': await MultipartFile.fromFile(path, filename: fileName),
    });
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'auth/linkedin-profile/import/',
      data: formData,
      options: Options(contentType: 'multipart/form-data'),
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
