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
      .replaceAllMapped(RegExp(r'\s+(#{1,6}\s+)'), (match) => '\n\n${match.group(1)}')
      .replaceAllMapped(RegExp(r'([^\n])\s+(\*\s+[A-Z0-9])'), (match) => '${match.group(1)}\n${match.group(2)}')
      .replaceAllMapped(RegExp(r'([^\n])\s+([•-]\s+[A-Z0-9])'), (match) => '${match.group(1)}\n${match.group(2)}')
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
  'Applied',
  'Screening',
  'Shortlist',
  'Interview',
  'Evaluation',
  'HR review',
  'Offer',
  'Hired',
];

const Map<String, int> _applicationPhaseIndexes = {
  'submitted': 0,
  'screened': 0,
  'screened_qualified': 1,
  'screened_not_qualified': 1,
  'shortlisted': 2,
  'interview_invited': 2,
  'interview_accepted': 3,
  'interview_declined': 3,
  'interviewing': 3,
  'evaluation_submitted': 4,
  'decision_pending': 5,
  'hr_approved': 5,
  'hr_rejected': 5,
  'offer_sent': 6,
  'offer_accepted': 6,
  'offer_declined': 6,
  'hired': 7,
};

int applicationPhaseIndex(String status) =>
    _applicationPhaseIndexes[status] ?? 0;

ApplicationStatusInfo applicationStatusInfo(String status) {
  switch (status) {
    case 'submitted':
      return const ApplicationStatusInfo(
        label: 'Applied',
        description: 'Your application was submitted successfully.',
        nextAction: 'Wait for the recruitment team to review your resume.',
      );
    case 'screened':
      return const ApplicationStatusInfo(
        label: 'Screening in progress',
        description: 'Your resume is being reviewed.',
        nextAction: 'No action is needed right now.',
      );
    case 'screened_qualified':
      return const ApplicationStatusInfo(
        label: 'Passed screening',
        description: 'Your application passed the screening stage.',
        nextAction: 'Wait for interview scheduling updates.',
      );
    case 'screened_not_qualified':
      return const ApplicationStatusInfo(
        label: 'Under recruiter review',
        description:
            'Screening found gaps, but the recruiter still reviews the application.',
        nextAction: 'Wait for the recruitment team decision.',
      );
    case 'shortlisted':
      return const ApplicationStatusInfo(
        label: 'Shortlisted',
        description: 'You were selected for the interview stage.',
        nextAction: 'Watch for an invitation to choose an interview slot.',
      );
    case 'interview_invited':
      return const ApplicationStatusInfo(
        label: 'Interview invitation sent',
        description: 'You have an interview scheduling invitation.',
        nextAction: 'Choose a suitable interview slot.',
      );
    case 'interview_accepted':
      return const ApplicationStatusInfo(
        label: 'Interview scheduled',
        description: 'Your interview slot is confirmed.',
        nextAction: 'Attend the interview at the scheduled time.',
      );
    case 'evaluation_submitted':
      return const ApplicationStatusInfo(
        label: 'Evaluation submitted',
        description: 'The interviewer submitted feedback for recruiter review.',
        nextAction: 'Wait for the hiring decision review.',
      );
    case 'decision_pending':
      return const ApplicationStatusInfo(
        label: 'Waiting for HR approval',
        description: 'The recruiter recommendation is being reviewed by HR.',
        nextAction: 'Wait for the final internal review.',
      );
    case 'hr_approved':
      return const ApplicationStatusInfo(
        label: 'Approved for offer',
        description: 'HR approved the hire recommendation.',
        nextAction: 'Wait for the official job offer.',
      );
    case 'offer_sent':
      return const ApplicationStatusInfo(
        label: 'Offer sent',
        description: 'A job offer has been sent to you.',
        nextAction: 'Review the offer and accept or decline it before the deadline.',
      );
    case 'offer_declined':
      return const ApplicationStatusInfo(
        label: 'Offer declined',
        description: 'You declined the job offer.',
        nextAction: 'No further action is required.',
      );
    case 'hired':
      return const ApplicationStatusInfo(
        label: 'Hired',
        description: 'You accepted the offer and the recruitment flow is complete.',
        nextAction: 'Wait for next steps from the organization.',
      );
    case 'rejected':
      return const ApplicationStatusInfo(
        label: 'Not selected',
        description: 'This application is no longer moving forward.',
        nextAction: 'You may apply for other open roles.',
      );
    case 'withdrawn':
      return const ApplicationStatusInfo(
        label: 'Withdrawn',
        description: 'You withdrew this application.',
        nextAction: 'No further action is required.',
      );
    default:
      return ApplicationStatusInfo(
        label: titleCaseStatus(status),
        description: 'This application is in a recruitment stage that needs review.',
        nextAction: 'Check back later for updates.',
      );
  }
}

String titleCaseStatus(String status) {
  if (status.isEmpty) return 'Unknown';
  return status
      .split('_')
      .map((part) => part.isEmpty ? part : '${part[0].toUpperCase()}${part.substring(1)}')
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
                    icon: Icon(job.isSaved ? Icons.bookmark : Icons.bookmark_border),
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
                  Chip(label: Text(job.location.isEmpty ? 'Remote/unspecified' : job.location)),
                  Chip(label: Text(job.employmentType.isEmpty ? 'Employment type n/a' : job.employmentType)),
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
