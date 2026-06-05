import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'api/api_client.dart';
import 'router/app_router.dart';
import 'services/token_storage.dart';

void main() {
  runApp(const HRRecruitApplicantApp());
}

class HRRecruitApplicantApp extends StatelessWidget {
  const HRRecruitApplicantApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<TokenStorage>(create: (_) => TokenStorage()),
        ProxyProvider<TokenStorage, ApiClient>(
          update: (_, tokenStorage, __) => ApiClient(tokenStorage: tokenStorage),
        ),
      ],
      child: MaterialApp.router(
        title: 'HRRecruit Applicant',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
          useMaterial3: true,
        ),
        routerConfig: appRouter,
      ),
    );
  }
}
