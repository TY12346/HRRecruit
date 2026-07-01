import 'dart:async';

import 'package:flutter/foundation.dart';

import '../models/applicant_profile.dart';
import '../services/applicant_auth_service.dart';
import '../services/push_notification_service.dart';
import '../services/token_storage.dart';

class AuthController extends ChangeNotifier {
  AuthController({
    required ApplicantAuthService authService,
    required TokenStorage tokenStorage,
    required PushNotificationService pushNotificationService,
  })  : _authService = authService,
        _tokenStorage = tokenStorage,
        _pushNotificationService = pushNotificationService;

  final ApplicantAuthService _authService;
  final TokenStorage _tokenStorage;
  final PushNotificationService _pushNotificationService;

  ApplicantProfile? _profile;
  bool _isInitialized = false;
  bool _isLoading = false;

  ApplicantProfile? get profile => _profile;
  bool get isInitialized => _isInitialized;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _profile != null;

  Future<void> initialize() async {
    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      _isInitialized = true;
      notifyListeners();
      return;
    }

    try {
      final profile = await _authService.getProfile();
      _ensureApplicant(profile);
      _profile = profile;
    } catch (_) {
      await _tokenStorage.clearTokens();
      _profile = null;
      _isInitialized = true;
      notifyListeners();
      return;
    }

    _registerPushDeviceAfterAuth();
    _isInitialized = true;
    notifyListeners();
  }

  Future<void> register({
    required String fullName,
    required String email,
    required String phoneNumber,
    required String password,
  }) async {
    await _runAuthAction(() async {
      final result = await _authService.register(
        fullName: fullName,
        email: email,
        phoneNumber: phoneNumber,
        password: password,
      );
      _ensureApplicant(result.user);
      await _tokenStorage.saveTokens(
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
      );
      _profile = result.user;
      _registerPushDeviceAfterAuth();
    });
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    await _runAuthAction(() async {
      final result = await _authService.login(email: email, password: password);
      _ensureApplicant(result.user);
      await _tokenStorage.saveTokens(
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
      );
      _profile = result.user;
      _registerPushDeviceAfterAuth();
    });
  }

  Future<void> requestPasswordReset({required String email}) async {
    await _runAuthAction(() async {
      await _authService.requestPasswordReset(email: email);
    });
  }

  Future<void> verifyPasswordResetOtp({
    required String email,
    required String otpCode,
  }) async {
    await _runAuthAction(
      () => _authService.verifyPasswordResetOtp(
        email: email,
        otpCode: otpCode,
      ),
    );
  }

  Future<void> confirmPasswordReset({
    required String email,
    required String otpCode,
    required String newPassword,
  }) async {
    await _runAuthAction(
      () => _authService.confirmPasswordReset(
        email: email,
        otpCode: otpCode,
        newPassword: newPassword,
      ),
    );
  }

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _runAuthAction(
      () => _authService.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
      ),
    );
  }

  Future<void> refreshProfile() async {
    final profile = await _authService.getProfile();
    _ensureApplicant(profile);
    _profile = profile;
    notifyListeners();
  }

  Future<void> updateProfile({
    required String fullName,
    required String phoneNumber,
    required String linkedinUrl,
    required String personalSummary,
    required List<ApplicantExperience> experiences,
    required List<ApplicantEducation> educations,
    required List<ApplicantSkill> skills,
  }) async {
    await _runAuthAction(() async {
      final profile = await _authService.updateProfile(
        fullName: fullName,
        phoneNumber: phoneNumber,
        linkedinUrl: linkedinUrl,
        personalSummary: personalSummary,
        experiences: experiences,
        educations: educations,
        skills: skills,
      );
      _ensureApplicant(profile);
      _profile = profile;
    });
  }

  Future<void> importLinkedInProfilePdf({
    required String path,
    required String fileName,
  }) async {
    await _runAuthAction(() async {
      final profile = await _authService.importLinkedInProfilePdf(
        path: path,
        fileName: fileName,
      );
      _ensureApplicant(profile);
      _profile = profile;
    });
  }

  Future<void> uploadResume({
    required String path,
    required String fileName,
  }) async {
    await _runAuthAction(() async {
      await _authService.uploadResume(path: path, fileName: fileName);
      final profile = await _authService.getProfile();
      _ensureApplicant(profile);
      _profile = profile;
    });
  }

  Future<void> logout() async {
    final refreshToken = await _tokenStorage.readRefreshToken();
    _isLoading = true;
    notifyListeners();

    try {
      if (refreshToken != null && refreshToken.isNotEmpty) {
        await _authService.logout(refreshToken: refreshToken);
      }
    } catch (_) {
      // Local logout still clears the stored JWT when the backend token blacklist
      // request fails or the token was already invalidated.
    } finally {
      await _tokenStorage.clearTokens();
      _profile = null;
      _isLoading = false;
      notifyListeners();
    }
  }

  void _ensureApplicant(ApplicantProfile profile) {
    if (profile.role != 'applicant') {
      throw Exception('Only applicant accounts can use the mobile app.');
    }
  }

  void _registerPushDeviceAfterAuth() {
    unawaited(_registerPushDeviceAfterAuthSafely());
  }

  Future<void> _registerPushDeviceAfterAuthSafely() async {
    try {
      await _pushNotificationService.registerDevice();
    } catch (error) {
      debugPrint(
        'Unable to register Firebase push device after authentication: $error',
      );
    }
  }

  Future<void> _runAuthAction(Future<void> Function() action) async {
    _isLoading = true;
    notifyListeners();
    try {
      await action();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
