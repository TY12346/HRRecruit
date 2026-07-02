import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../controllers/auth_controller.dart';
import '../../models/applicant_profile.dart';
import '../../models/job_posting.dart';
import '../../services/job_discovery_service.dart';
import '../auth_form_helpers.dart';
import '../../widgets/app_navigation.dart';
import 'job_cards.dart';

class JobDetailScreen extends StatefulWidget {
  const JobDetailScreen({super.key, required this.jobId});

  final int jobId;

  @override
  State<JobDetailScreen> createState() => _JobDetailScreenState();
}

class _JobDetailScreenState extends State<JobDetailScreen> {
  late Future<JobPosting> _jobFuture;
  bool _isSaving = false;
  bool _isApplying = false;

  @override
  void initState() {
    super.initState();
    _jobFuture = _loadJob();
  }

  Future<JobPosting> _loadJob() {
    return context.read<JobDiscoveryService>().getJob(widget.jobId);
  }

  void _refresh() {
    setState(() {
      _jobFuture = _loadJob();
    });
  }

  Future<void> _toggleSaved(JobPosting job) async {
    setState(() => _isSaving = true);
    final service = context.read<JobDiscoveryService>();
    try {
      if (job.isSaved) {
        await service.unsaveJob(job.id);
      } else {
        await service.saveJob(job.id);
      }
      _refresh();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  Future<void> _apply(JobPosting job) async {
    final resumes =
        context.read<AuthController>().profile?.resumes ??
        const <ApplicantResume>[];
    if (resumes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Upload a resume before applying.')),
      );
      context.push('/resume');
      return;
    }

    final selectedResume = await _selectResumeForApplication(resumes);
    if (selectedResume == null) {
      return;
    }

    setState(() => _isApplying = true);
    try {
      final application = await context.read<JobDiscoveryService>().applyForJob(
            job.id,
            resumeId: selectedResume.id,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Application submitted with ${_resumeLabel(selectedResume)}.',
          ),
        ),
      );
      context.push('/applications/${application.id}');
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) setState(() => _isApplying = false);
    }
  }

  Future<ApplicantResume?> _selectResumeForApplication(
    List<ApplicantResume> resumes,
  ) {
    return showModalBottomSheet<ApplicantResume>(
      context: context,
      showDragHandle: true,
      builder: (bottomSheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Select resume for this application',
                style: Theme.of(bottomSheetContext).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              const Text(
                'Choose the resume you want recruiters to review for this job.',
              ),
              const SizedBox(height: 12),
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    for (final resume in resumes)
                      Card.outlined(
                        child: ListTile(
                          leading: const Icon(Icons.description_outlined),
                          title: Text(_resumeLabel(resume)),
                          subtitle: Text(resume.resumeFile.split('/').last),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () =>
                              Navigator.of(bottomSheetContext).pop(resume),
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () {
                  Navigator.of(bottomSheetContext).pop();
                  context.push('/resume');
                },
                icon: const Icon(Icons.upload_file_outlined),
                label: const Text('Manage resumes'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _resumeLabel(ApplicantResume resume) {
    final title = resume.title.trim();
    if (title.isNotEmpty) return title;
    return resume.resumeFile.split('/').last;
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Job details'),
        body: SafeArea(
          child: FutureBuilder<JobPosting>(
            future: _jobFuture,
            builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return _DetailError(error: snapshot.error!, onRetry: _refresh);
            }
            final job = snapshot.data!;
            return ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(
                  job.title,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 6),
                Text(
                  job.organizationName,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    Chip(
                      label: Text(
                        job.location.isEmpty ? 'Location n/a' : job.location,
                      ),
                    ),
                    Chip(
                      label: Text(
                        job.employmentType.isEmpty
                            ? 'Type n/a'
                            : job.employmentType,
                      ),
                    ),
                    Chip(label: Text(formatMoney(job.approximateSalary))),
                    Chip(label: Text(titleCaseStatus(job.status))),
                  ],
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _isSaving ? null : () => _toggleSaved(job),
                        icon: Icon(
                          job.isSaved ? Icons.bookmark : Icons.bookmark_border,
                        ),
                        label: Text(job.isSaved ? 'Unsave job' : 'Save job'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: _isApplying || job.status != 'open'
                            ? null
                            : () => _apply(job),
                        icon: const Icon(Icons.send_outlined),
                        label: Text(_isApplying ? 'Applying...' : 'Apply'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Text(
                  'Description',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  job.description.isEmpty
                      ? 'No description provided.'
                      : formatJobDescriptionText(job.description),
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.5),
                ),
                const SizedBox(height: 24),
                Text(
                  'Requirements',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                if (job.requirements.isEmpty)
                  const Text('No requirements configured yet.')
                else
                  ...job.requirements.map(
                    (requirement) => Card(
                      child: ListTile(
                        title: Text(requirement.description),
                        subtitle: Text(
                          '${titleCaseStatus(requirement.requirementType)} · '
                          'Weight ${(requirement.weightScore * 100).toStringAsFixed(0)}% · '
                          'Threshold ${(requirement.minimumThreshold * 100).toStringAsFixed(0)}%',
                        ),
                      ),
                    ),
                  ),
                const SizedBox(height: 24),
                Text('Posted ${formatDate(job.createdAt)}'),
              ],
            );
            },
          ),
        ),
      ),
    );
  }
}

class _DetailError extends StatelessWidget {
  const _DetailError({required this.error, required this.onRetry});

  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48),
            const SizedBox(height: 12),
            Text(readableApiError(error), textAlign: TextAlign.center),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
