import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../controllers/auth_controller.dart';

class ApplicantHomeScreen extends StatelessWidget {
  const ApplicantHomeScreen({super.key});

  Future<void> _logout(BuildContext context) async {
    await context.read<AuthController>().logout();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    final profile = auth.profile;

    final homeActions = <_ApplicantHomeAction>[
      const _ApplicantHomeAction(
        icon: Icons.search,
        title: 'Find jobs',
        subtitle: 'Search and filter open job postings',
        route: '/jobs',
      ),
      const _ApplicantHomeAction(
        icon: Icons.bookmark_border,
        title: 'Saved jobs',
        subtitle: 'Review jobs you saved for later',
        route: '/saved-jobs',
      ),
      const _ApplicantHomeAction(
        icon: Icons.assignment_outlined,
        title: 'My applications',
        subtitle: 'Track application status and history',
        route: '/applications',
      ),
      const _ApplicantHomeAction(
        icon: Icons.schedule_outlined,
        title: 'Schedule interviews',
        subtitle: 'Choose interview times from recruiter requests',
        route: '/interview-scheduling',
      ),
      const _ApplicantHomeAction(
        icon: Icons.event_outlined,
        title: 'My interviews',
        subtitle: 'View upcoming and completed interviews',
        route: '/interviews',
      ),
      const _ApplicantHomeAction(
        icon: Icons.card_giftcard_outlined,
        title: 'Job offers',
        subtitle: 'Review and respond to job offers',
        route: '/job-offers',
      ),
      const _ApplicantHomeAction(
        icon: Icons.notifications_outlined,
        title: 'Notifications',
        subtitle: 'Read application, interview, and offer updates',
        route: '/notifications',
      ),
      const _ApplicantHomeAction(
        icon: Icons.person_outline,
        title: 'Profile',
        subtitle: 'View and edit your applicant information',
        route: '/profile',
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Applicant home'),
        actions: [
          IconButton(
            tooltip: 'Logout',
            onPressed: auth.isLoading ? null : () => _logout(context),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text(
              'Hello, ${profile?.fullName.isNotEmpty == true ? profile!.fullName : 'Applicant'}',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            const Text('Keep your profile and resume current for recruiter screening.'),
            const SizedBox(height: 24),
            for (final action in homeActions) _homeActionCard(context, action),
            _homeActionCard(
              context,
              _ApplicantHomeAction(
                icon: Icons.upload_file_outlined,
                title: 'Resume upload',
                subtitle: profile?.resumeFile == null || profile!.resumeFile!.isEmpty
                    ? 'Upload a PDF or DOCX resume'
                    : 'Resume on file. Tap to replace it.',
                route: '/resume',
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _homeActionCard(BuildContext context, _ApplicantHomeAction action) {
    return Card(
      child: ListTile(
        leading: Icon(action.icon),
        title: Text(action.title),
        subtitle: Text(action.subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push(action.route),
      ),
    );
  }
}

class _ApplicantHomeAction {
  const _ApplicantHomeAction({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.route,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final String route;
}
