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
            Card(
              child: ListTile(
                leading: const Icon(Icons.person_outline),
                title: const Text('Profile'),
                subtitle: const Text('View and edit your applicant information'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.go('/profile'),
              ),
            ),
            Card(
              child: ListTile(
                leading: const Icon(Icons.upload_file_outlined),
                title: const Text('Resume upload'),
                subtitle: Text(
                  profile?.resumeFile == null || profile!.resumeFile!.isEmpty
                      ? 'Upload a PDF or DOCX resume'
                      : 'Resume on file. Tap to replace it.',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.go('/resume'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
