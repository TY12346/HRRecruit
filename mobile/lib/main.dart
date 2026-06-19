import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'api/api_client.dart';
import 'controllers/auth_controller.dart';
import 'router/app_router.dart';
import 'services/applicant_auth_service.dart';
import 'services/applicant_workflow_service.dart';
import 'services/job_discovery_service.dart';
import 'services/linkedin_oauth_service.dart';
import 'services/token_storage.dart';

void main() {
  runApp(const HRRecruitApplicantApp());
}

class HRRecruitApplicantApp extends StatefulWidget {
  const HRRecruitApplicantApp({super.key});

  @override
  State<HRRecruitApplicantApp> createState() => _HRRecruitApplicantAppState();
}

class _HRRecruitApplicantAppState extends State<HRRecruitApplicantApp> {
  late final TokenStorage _tokenStorage;
  late final ApiClient _apiClient;
  late final ApplicantAuthService _authService;
  late final AuthController _authController;
  late final GoRouter _router;

  @override
  void initState() {
    super.initState();
    _tokenStorage = TokenStorage();
    _apiClient = ApiClient(tokenStorage: _tokenStorage);
    _authService = ApplicantAuthService(_apiClient);
    _authController = AuthController(
      authService: _authService,
      tokenStorage: _tokenStorage,
    )..initialize();
    _router = createAppRouter(_authController);
  }

  @override
  void dispose() {
    _router.dispose();
    _authController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<TokenStorage>.value(value: _tokenStorage),
        Provider<ApiClient>.value(value: _apiClient),
        Provider<ApplicantAuthService>.value(value: _authService),
        Provider<JobDiscoveryService>(
          create: (_) => JobDiscoveryService(_apiClient),
        ),
        Provider<LinkedInOAuthService>(
          create: (_) => LinkedInOAuthService(),
        ),
        Provider<ApplicantWorkflowService>(
          create: (_) => ApplicantWorkflowService(_apiClient),
        ),
        ChangeNotifierProvider<AuthController>.value(value: _authController),
      ],
      child: MaterialApp.router(
        title: 'HRRecruit Applicant',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
          useMaterial3: true,
        ),
        routerConfig: _router,
      ),
    );
  }
}
