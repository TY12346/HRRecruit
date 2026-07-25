import 'package:flutter/material.dart';

import '../../models/job_application.dart';
import '../../models/job_posting.dart';

String formatDate(DateTime? value) {
  if (value == null) return 'Not available';
  final local = value.toLocal();
  return '${local.year.toString().padLeft(4, '0')}-'
      '${local.month.toString().padLeft(2, '0')}-'
      '${local.day.toString().padLeft(2, '0')}';
}

String formatDateTime(DateTime? value) {
  if (value == null) return 'Not available';
  final local = value.toLocal();
  return '${formatDate(local)} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}

String formatMoney(double value) {
  if (value <= 0) return 'Salary not specified';
  return 'RM ${value.toStringAsFixed(2)}';
}

String formatJobDescriptionText(String value) {
  if (value.trim().isEmpty) return '';
  return value
      .replaceAll(RegExp(r'\r\n?'), '\n')
      .replaceAllMapped(
          RegExp(r'\s+(#{1,6}\s+)'), (match) => '\n\n${match.group(1)}')
      .replaceAllMapped(RegExp(r'([^\n])\s+(\*\s+[A-Z0-9])'),
          (match) => '${match.group(1)}\n${match.group(2)}')
      .replaceAllMapped(RegExp(r'([^\n])\s+([•-]\s+[A-Z0-9])'),
          (match) => '${match.group(1)}\n${match.group(2)}')
      .replaceAll(RegExp(r'\n{3,}'), '\n\n')
      .trim();
}

class ApplicationStatusInfo {
  const ApplicationStatusInfo({
    required this.label,
    required this.description,
    required this.nextAction,
  });

  final String label;
  final String description;
  final String nextAction;
}

const List<String> applicationFlowPhases = [
  'Under review',
  'Rejected',
];

const Map<String, int> _applicationPhaseIndexes = {
  'under_review': 0,
  'rejected': 1,
};

int applicationPhaseIndex(String status) =>
    _applicationPhaseIndexes[status] ?? 0;

ApplicationStatusInfo applicationStatusInfo(String status) {
  switch (status) {
    case 'under_review':
      return const ApplicationStatusInfo(
        label: 'Under review',
        description: 'Your application is being reviewed by the recruitment team.',
        nextAction: 'Watch for interview invitations and offer updates.',
      );
    case 'rejected':
      return const ApplicationStatusInfo(
        label: 'Rejected',
        description: 'This application is no longer moving forward.',
        nextAction: 'You may apply for other open roles.',
      );
    default:
      return ApplicationStatusInfo(
        label: titleCaseStatus(status),
        description: 'This application status needs review.',
        nextAction: 'Check back later for updates.',
      );
  }
}

String titleCaseStatus(String status) {
  if (status.isEmpty) return 'Unknown';
  return status
      .split('_')
      .map((part) =>
          part.isEmpty ? part : '${part[0].toUpperCase()}${part.substring(1)}')
      .join(' ');
}

class JobSummaryCard extends StatelessWidget {
  const JobSummaryCard({
    super.key,
    required this.job,
    required this.onTap,
    this.onSaveToggle,
  });

  final JobPosting job;
  final VoidCallback onTap;
  final VoidCallback? onSaveToggle;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      job.title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  IconButton(
                    tooltip: job.isSaved ? 'Unsave job' : 'Save job',
                    onPressed: onSaveToggle,
                    icon: Icon(
                        job.isSaved ? Icons.bookmark : Icons.bookmark_border),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(job.organizationName),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  Chip(
                      label: Text(job.location.isEmpty
                          ? 'Remote/unspecified'
                          : job.location)),
                  Chip(
                      label: Text(job.employmentType.isEmpty
                          ? 'Employment type n/a'
                          : job.employmentType)),
                  Chip(label: Text(formatMoney(job.approximateSalary))),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ApplicationSummaryCard extends StatelessWidget {
  const ApplicationSummaryCard({
    super.key,
    required this.application,
    required this.onTap,
  });

  final JobApplication application;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(application.jobTitle),
        subtitle: Text(
          '${application.organizationName}\nApplied ${formatDate(application.appliedAt)}',
        ),
        isThreeLine: true,
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(applicationStatusInfo(application.status).label),
            const Icon(Icons.chevron_right),
          ],
        ),
        onTap: onTap,
      ),
    );
  }
}
