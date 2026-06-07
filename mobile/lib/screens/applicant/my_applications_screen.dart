import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/job_application.dart';
import '../../services/job_discovery_service.dart';
import '../auth_form_helpers.dart';
import 'job_cards.dart';

class MyApplicationsScreen extends StatefulWidget {
  const MyApplicationsScreen({super.key});

  @override
  State<MyApplicationsScreen> createState() => _MyApplicationsScreenState();
}

class _MyApplicationsScreenState extends State<MyApplicationsScreen> {
  late Future<List<JobApplication>> _applicationsFuture;

  @override
  void initState() {
    super.initState();
    _applicationsFuture = _loadApplications();
  }

  Future<List<JobApplication>> _loadApplications() {
    return context.read<JobDiscoveryService>().getApplications();
  }

  void _refresh() {
    setState(() {
      _applicationsFuture = _loadApplications();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My applications')),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            _refresh();
            await _applicationsFuture;
          },
          child: FutureBuilder<List<JobApplication>>(
            future: _applicationsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return _ApplicationsMessage(
                  icon: Icons.error_outline,
                  title: 'Could not load applications',
                  message: readableApiError(snapshot.error!),
                  action: OutlinedButton(onPressed: _refresh, child: const Text('Retry')),
                );
              }
              final applications = snapshot.data ?? [];
              if (applications.isEmpty) {
                return _ApplicationsMessage(
                  icon: Icons.assignment_outlined,
                  title: 'No applications yet',
                  message: 'Apply to open jobs to track your application progress here.',
                  action: FilledButton(
                    onPressed: () => context.go('/jobs'),
                    child: const Text('Find jobs'),
                  ),
                );
              }
              return ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: applications.length,
                itemBuilder: (context, index) {
                  final application = applications[index];
                  return ApplicationSummaryCard(
                    application: application,
                    onTap: () => context.go('/applications/${application.id}'),
                  );
                },
              );
            },
          ),
        ),
      ),
    );
  }
}

class _ApplicationsMessage extends StatelessWidget {
  const _ApplicationsMessage({
    required this.icon,
    required this.title,
    required this.message,
    this.action,
  });

  final IconData icon;
  final String title;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(32),
      children: [
        Icon(icon, size: 56),
        const SizedBox(height: 12),
        Text(title, style: Theme.of(context).textTheme.titleMedium, textAlign: TextAlign.center),
        const SizedBox(height: 8),
        Text(message, textAlign: TextAlign.center),
        if (action != null) ...[
          const SizedBox(height: 16),
          Center(child: action),
        ],
      ],
    );
  }
}
