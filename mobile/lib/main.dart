import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'api/api_client.dart';
import 'controllers/auth_controller.dart';
import 'router/app_router.dart';
import 'services/applicant_auth_service.dart';
import 'services/token_storage.dart';

void main() {
  runApp(const HRRecruitApplicantApp());
}

class HRRecruitApplicantApp extends StatelessWidget {
  const HRRecruitApplicantApp({super.key});

  @override
  Widget build(BuildContext context) {
    final tokenStorage = TokenStorage();
    final apiClient = ApiClient(tokenStorage: tokenStorage);
    final authService = ApplicantAuthService(apiClient);

    return MultiProvider(
      providers: [
        Provider<TokenStorage>.value(value: tokenStorage),
        Provider<ApiClient>.value(value: apiClient),
        Provider<ApplicantAuthService>.value(value: authService),
        ChangeNotifierProvider<AuthController>(
          create: (_) => AuthController(
            authService: authService,
            tokenStorage: tokenStorage,
          )..initialize(),
        ),
      ],
      child: Consumer<AuthController>(
        builder: (context, authController, _) {
          return MaterialApp.router(
            title: 'HRRecruit Applicant',
            debugShowCheckedModeBanner: false,
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
              useMaterial3: true,
            ),
            routerConfig: createAppRouter(authController),
          );
        },
      ),
    );
  }
}
