import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/job_posting.dart';
import '../../services/job_discovery_service.dart';
import '../auth_form_helpers.dart';
import 'job_cards.dart';
import '../../widgets/app_navigation.dart';

class JobSearchScreen extends StatefulWidget {
  const JobSearchScreen({super.key});

  @override
  State<JobSearchScreen> createState() => _JobSearchScreenState();
}

class _JobSearchScreenState extends State<JobSearchScreen> {
  final _searchController = TextEditingController();
  final _locationController = TextEditingController();
  final _employmentTypeController = TextEditingController();
  late Future<List<JobPosting>> _jobsFuture;

  @override
  void initState() {
    super.initState();
    _jobsFuture = _loadJobs();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _locationController.dispose();
    _employmentTypeController.dispose();
    super.dispose();
  }

  Future<List<JobPosting>> _loadJobs() {
    return context.read<JobDiscoveryService>().searchJobs(
          search: _searchController.text,
          location: _locationController.text,
          employmentType: _employmentTypeController.text,
        );
  }

  void _search() {
    setState(() {
      _jobsFuture = _loadJobs();
    });
  }

  void _clearFilters() {
    _searchController.clear();
    _locationController.clear();
    _employmentTypeController.clear();
    _search();
  }

  Future<void> _toggleSaved(JobPosting job) async {
    final service = context.read<JobDiscoveryService>();
    try {
      if (job.isSaved) {
        await service.unsaveJob(job.id);
      } else {
        await service.saveJob(job.id);
      }
      _search();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Find jobs'),
        body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            _search();
            await _jobsFuture;
          },
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              TextField(
                controller: _searchController,
                textInputAction: TextInputAction.search,
                decoration: const InputDecoration(
                  labelText: 'Search title or description',
                  prefixIcon: Icon(Icons.search),
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (_) => _search(),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _locationController,
                      decoration: const InputDecoration(
                        labelText: 'Location',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _employmentTypeController,
                      decoration: const InputDecoration(
                        labelText: 'Employment type',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: _search,
                      icon: const Icon(Icons.tune),
                      label: const Text('Apply filters'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  TextButton(onPressed: _clearFilters, child: const Text('Clear')),
                ],
              ),
              const SizedBox(height: 16),
              FutureBuilder<List<JobPosting>>(
                future: _jobsFuture,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: Padding(
                      padding: EdgeInsets.all(32),
                      child: CircularProgressIndicator(),
                    ));
                  }
                  if (snapshot.hasError) {
                    return _ErrorState(error: snapshot.error!, onRetry: _search);
                  }
                  final jobs = snapshot.data ?? [];
                  if (jobs.isEmpty) {
                    return const _EmptyState(
                      icon: Icons.work_outline,
                      title: 'No open jobs found',
                      message: 'Try changing your search keyword, location, or employment type.',
                    );
                  }
                  return Column(
                    children: jobs
                        .map(
                          (job) => JobSummaryCard(
                            job: job,
                            onTap: () => context.push('/jobs/${job.id}'),
                            onSaveToggle: () => _toggleSaved(job),
                          ),
                        )
                        .toList(),
                  );
                },
              ),
            ],
          ),
        ),
      ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.error, required this.onRetry});

  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Icon(Icons.error_outline, size: 48),
        const SizedBox(height: 12),
        Text(readableApiError(error), textAlign: TextAlign.center),
        const SizedBox(height: 12),
        OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.icon, required this.title, required this.message});

  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        children: [
          Icon(icon, size: 56),
          const SizedBox(height: 12),
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(message, textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
