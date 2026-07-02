import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/job_application.dart';
import '../../services/job_discovery_service.dart';
import '../auth_form_helpers.dart';
import 'job_cards.dart';
import '../../widgets/app_navigation.dart';

class ApplicationDetailScreen extends StatefulWidget {
  const ApplicationDetailScreen({super.key, required this.applicationId});

  final int applicationId;

  @override
  State<ApplicationDetailScreen> createState() => _ApplicationDetailScreenState();
}

class _ApplicationDetailScreenState extends State<ApplicationDetailScreen> {
  late Future<_ApplicationDetailData> _detailFuture;
  bool _isWithdrawing = false;

  @override
  void initState() {
    super.initState();
    _detailFuture = _loadDetail();
  }

  Future<_ApplicationDetailData> _loadDetail() async {
    final service = context.read<JobDiscoveryService>();
    final application = await service.getApplication(widget.applicationId);
    final history = await service.getApplicationHistory(widget.applicationId);
    return _ApplicationDetailData(application: application, history: history);
  }

  void _refresh() {
    setState(() {
      _detailFuture = _loadDetail();
    });
  }

  Future<void> _withdraw(JobApplication application) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Withdraw application?'),
        content: const Text('You can only withdraw while the application is submitted or screened.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Withdraw')),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _isWithdrawing = true);
    try {
      await context.read<JobDiscoveryService>().withdrawApplication(application.jobId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Application withdrawn.')),
      );
      _refresh();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) setState(() => _isWithdrawing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Application details'),
        body: SafeArea(
          child: FutureBuilder<_ApplicationDetailData>(
          future: _detailFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return _ApplicationDetailError(error: snapshot.error!, onRetry: _refresh);
            }
            final data = snapshot.data!;
            final application = data.application;
            final statusInfo = applicationStatusInfo(application.status);
            return ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(
                  application.jobTitle,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 6),
                Text(
                  application.organizationName,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    Chip(label: Text(statusInfo.label)),
                    Chip(label: Text('Applied ${formatDate(application.appliedAt)}')),
                    if (application.finalScore != null)
                      Chip(
                        label: Text(
                          'AI score ${application.finalScore!.toStringAsFixed(2)}',
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 20),
                ApplicationFlowCard(status: application.status),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => context.push('/jobs/${application.jobId}'),
                        icon: const Icon(Icons.work_outline),
                        label: const Text('View job'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: application.canWithdraw && !_isWithdrawing
                            ? () => _withdraw(application)
                            : null,
                        icon: const Icon(Icons.undo),
                        label: Text(_isWithdrawing ? 'Withdrawing...' : 'Withdraw'),
                      ),
                    ),
                  ],
                ),
                if (application.recruiterRemark.isNotEmpty) ...[
                  const SizedBox(height: 24),
                  Text(
                    'Recruiter remark',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(application.recruiterRemark),
                ],
                const SizedBox(height: 24),
                Text(
                  'Status history',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                if (data.history.isEmpty)
                  const Text('No status history is available yet.')
                else
                  ...data.history.map(
                    (history) => TimelineTile(history: history),
                  ),
              ],
            );
          },
          ),
        ),
      ),
    );
  }
}

class ApplicationFlowCard extends StatelessWidget {
  const ApplicationFlowCard({super.key, required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final info = applicationStatusInfo(status);
    final currentIndex = applicationPhaseIndex(status);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Current stage: ${info.label}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 6),
            Text(info.description),
            const SizedBox(height: 6),
            Text(
              'Next action: ${info.nextAction}',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (var i = 0; i < applicationFlowPhases.length; i++)
                  Chip(
                    label: Text(applicationFlowPhases[i]),
                    backgroundColor: i == currentIndex
                        ? Theme.of(context).colorScheme.primaryContainer
                        : i < currentIndex
                            ? Theme.of(context).colorScheme.secondaryContainer
                            : null,
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class TimelineTile extends StatelessWidget {
  const TimelineTile({super.key, required this.history});

  final ApplicationStageHistory history;

  @override
  Widget build(BuildContext context) {
    final fromStage = applicationStatusInfo(history.fromStage).label;
    final toStage = applicationStatusInfo(history.toStage).label;
    return Card(
      child: ListTile(
        leading: const Icon(Icons.history),
        title: Text(fromStage == toStage ? toStage : '$fromStage → $toStage'),
        subtitle: Text(
          '${history.note.isEmpty ? 'Status updated.' : history.note}\n'
          '${formatDateTime(history.changedAt)} by ${history.changedByName}',
        ),
        isThreeLine: true,
      ),
    );
  }
}

class _ApplicationDetailError extends StatelessWidget {
  const _ApplicationDetailError({required this.error, required this.onRetry});

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

class _ApplicationDetailData {
  const _ApplicationDetailData({required this.application, required this.history});

  final JobApplication application;
  final List<ApplicationStageHistory> history;
}
