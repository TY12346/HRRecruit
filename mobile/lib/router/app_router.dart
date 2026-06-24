import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../controllers/auth_controller.dart';
import '../screens/applicant/application_detail_screen.dart';
import '../screens/applicant/interview_scheduling_requests_screen.dart';
import '../screens/applicant/job_offers_screen.dart';
import '../screens/applicant/job_detail_screen.dart';
import '../screens/applicant/job_search_screen.dart';
import '../screens/applicant/my_applications_screen.dart';
import '../screens/applicant/my_interviews_screen.dart';
import '../screens/applicant/notifications_screen.dart';
import '../screens/applicant/saved_jobs_screen.dart';
import '../screens/applicant_home_screen.dart';
import '../screens/forgot_password_screen.dart';
import '../screens/login_screen.dart';
import '../screens/profile_screen.dart';
import '../screens/register_screen.dart';
import '../screens/resume_upload_screen.dart';

GoRouter createAppRouter(AuthController authController) {
  return GoRouter(
    initialLocation: '/',
    refreshListenable: authController,
    redirect: (context, state) {
      if (!authController.isInitialized) {
        return state.matchedLocation == '/' ? null : '/';
      }

      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register' ||
          state.matchedLocation == '/forgot-password';
      if (!authController.isAuthenticated && !isAuthRoute) {
        return '/login';
      }
      if (authController.isAuthenticated && isAuthRoute) {
        return '/home';
      }
      if (authController.isAuthenticated && state.matchedLocation == '/') {
        return '/home';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const _SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const ApplicantHomeScreen(),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/resume',
        builder: (context, state) => const ResumeUploadScreen(),
      ),
      GoRoute(
        path: '/jobs',
        builder: (context, state) => const JobSearchScreen(),
      ),
      GoRoute(
        path: '/jobs/:jobId',
        builder: (context, state) => JobDetailScreen(
          jobId: int.parse(state.pathParameters['jobId']!),
        ),
      ),
      GoRoute(
        path: '/saved-jobs',
        builder: (context, state) => const SavedJobsScreen(),
      ),
      GoRoute(
        path: '/applications',
        builder: (context, state) => const MyApplicationsScreen(),
      ),
      GoRoute(
        path: '/applications/:applicationId',
        builder: (context, state) => ApplicationDetailScreen(
          applicationId: int.parse(state.pathParameters['applicationId']!),
        ),
      ),
      GoRoute(
        path: '/interview-scheduling',
        builder: (context, state) => const InterviewSchedulingRequestsScreen(),
      ),
      GoRoute(
        path: '/interviews',
        builder: (context, state) => const MyInterviewsScreen(),
      ),
      GoRoute(
        path: '/job-offers',
        builder: (context, state) => const JobOffersScreen(),
      ),
      GoRoute(
        path: '/notifications',
        builder: (context, state) => const NotificationsScreen(),
      ),

    ],
  );
}

class _SplashScreen extends StatelessWidget {
  const _SplashScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator()),
    );
  }
}
