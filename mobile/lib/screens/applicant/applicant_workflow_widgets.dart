import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher_string.dart';

import '../../models/applicant_interview.dart';
import '../../models/job_offer.dart';
import '../auth_form_helpers.dart';
import 'job_cards.dart';

class ApplicantWorkflowMessage extends StatelessWidget {
  const ApplicantWorkflowMessage({
    super.key,
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

class InterviewInvitationCard extends StatelessWidget {
  const InterviewInvitationCard({
    super.key,
    required this.invitation,
    required this.onTap,
  });

  final InterviewInvitation invitation;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final application = invitation.application;
    return Card(
      child: ListTile(
        leading: const Icon(Icons.event_available_outlined),
        title: Text(application?.jobTitle.isNotEmpty == true ? application!.jobTitle : 'Interview invitation'),
        subtitle: Text(
          '${application?.organizationName.isNotEmpty == true ? application!.organizationName : 'Organization not available'}\n'
          '${formatDateTime(invitation.proposedDatetime)} • ${titleCaseStatus(invitation.mode)}',
        ),
        isThreeLine: true,
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(titleCaseStatus(invitation.status)),
            const Icon(Icons.chevron_right),
          ],
        ),
        onTap: onTap,
      ),
    );
  }
}

class InterviewCard extends StatelessWidget {
  const InterviewCard({super.key, required this.interview});

  final ApplicantInterview interview;

  @override
  Widget build(BuildContext context) {
    final application = interview.application;
    final when = interview.scheduledDatetime ?? interview.latestInvitation?.proposedDatetime;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              application?.jobTitle.isNotEmpty == true ? application!.jobTitle : 'Interview',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(application?.organizationName.isNotEmpty == true ? application!.organizationName : 'Organization not available'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                Chip(label: Text(titleCaseStatus(interview.status))),
                Chip(label: Text(formatDateTime(when))),
                Chip(label: Text(titleCaseStatus(interview.mode))),
              ],
            ),
            if (interview.interviewerName.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('Interviewer: ${interview.interviewerName}'),
            ],
            if (interview.location.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('Location: ${interview.location}'),
            ],
            if (interview.meetingLink.isNotEmpty || interview.calendarLink.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: [
                  if (interview.meetingLink.isNotEmpty)
                    OutlinedButton.icon(
                      onPressed: () => launchUrlString(interview.meetingLink),
                      icon: const Icon(Icons.video_call_outlined),
                      label: const Text('Meeting link'),
                    ),
                  if (interview.calendarLink.isNotEmpty)
                    OutlinedButton.icon(
                      onPressed: () => launchUrlString(interview.calendarLink),
                      icon: const Icon(Icons.calendar_month_outlined),
                      label: const Text('Calendar'),
                    ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class JobOfferCard extends StatelessWidget {
  const JobOfferCard({
    super.key,
    required this.offer,
    required this.onAccept,
    required this.onDecline,
    required this.isBusy,
  });

  final JobOffer offer;
  final VoidCallback onAccept;
  final VoidCallback onDecline;
  final bool isBusy;

  @override
  Widget build(BuildContext context) {
    final application = offer.application;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              application?.jobTitle.isNotEmpty == true ? application!.jobTitle : 'Job offer',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(application?.organizationName.isNotEmpty == true ? application!.organizationName : 'Organization not available'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                Chip(label: Text(titleCaseStatus(offer.offerStatus))),
                Chip(label: Text('Deadline ${formatDateTime(offer.respondDeadline)}')),
              ],
            ),
            const SizedBox(height: 12),
            Text(offer.offerMessage),
            if (offer.offerLetterUrl.isNotEmpty) ...[
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () => launchUrlString(offer.offerLetterUrl),
                icon: const Icon(Icons.description_outlined),
                label: const Text('Open offer letter'),
              ),
            ],
            if (offer.canRespond) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: isBusy ? null : onDecline,
                      icon: const Icon(Icons.close),
                      label: const Text('Decline'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: isBusy ? null : onAccept,
                      icon: const Icon(Icons.check),
                      label: const Text('Accept'),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class ApiErrorMessage extends StatelessWidget {
  const ApiErrorMessage({super.key, required this.error, required this.onRetry});

  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ApplicantWorkflowMessage(
      icon: Icons.error_outline,
      title: 'Could not load data',
      message: readableApiError(error),
      action: OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
    );
  }
}
