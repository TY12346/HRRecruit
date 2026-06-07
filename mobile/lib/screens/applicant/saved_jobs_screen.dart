import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/job_posting.dart';
import '../../services/job_discovery_service.dart';
import '../auth_form_helpers.dart';
import 'job_cards.dart';

class SavedJobsScreen extends StatefulWidget {
  const SavedJobsScreen({super.key});

  @override
  State<SavedJobsScreen> createState() => _SavedJobsScreenState();
}

class _SavedJobsScreenState extends State<SavedJobsScreen> {
  late Future<List<JobPosting>> _savedJobsFuture;

  @override
  void initState() {
    super.initState();
    _savedJobsFuture = _loadSavedJobs();
  }

  Future<List<JobPosting>> _loadSavedJobs() {
    return context.read<JobDiscoveryService>().getSavedJobs();
  }

  void _refresh() {
    setState(() {
      _savedJobsFuture = _loadSavedJobs();
    });
  }

  Future<void> _unsave(JobPosting job) async {
    try {
      await context.read<JobDiscoveryService>().unsaveJob(job.id);
      _refresh();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Saved jobs')),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            _refresh();
            await _savedJobsFuture;
          },
          child: FutureBuilder<List<JobPosting>>(
            future: _savedJobsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return _SavedJobsMessage(
                  icon: Icons.error_outline,
                  title: 'Could not load saved jobs',
                  message: readableApiError(snapshot.error!),
                  action: OutlinedButton(onPressed: _refresh, child: const Text('Retry')),
                );
              }
              final jobs = snapshot.data ?? [];
              if (jobs.isEmpty) {
                return const _SavedJobsMessage(
                  icon: Icons.bookmark_border,
                  title: 'No saved jobs yet',
                  message: 'Save jobs from search results to review them later.',
                );
              }
              return ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: jobs.length,
                itemBuilder: (context, index) {
                  final job = jobs[index];
                  return JobSummaryCard(
                    job: job,
                    onTap: () => context.go('/jobs/${job.id}'),
                    onSaveToggle: () => _unsave(job),
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

class _SavedJobsMessage extends StatelessWidget {
  const _SavedJobsMessage({
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
