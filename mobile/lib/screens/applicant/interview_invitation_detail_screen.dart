import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher_string.dart';

import '../../models/applicant_interview.dart';
import '../../services/applicant_workflow_service.dart';
import '../auth_form_helpers.dart';
import 'applicant_workflow_widgets.dart';
import 'job_cards.dart';
import '../../widgets/app_navigation.dart';

class InterviewInvitationDetailScreen extends StatefulWidget {
  const InterviewInvitationDetailScreen({super.key, required this.invitationId});

  final int invitationId;

  @override
  State<InterviewInvitationDetailScreen> createState() => _InterviewInvitationDetailScreenState();
}

class _InterviewInvitationDetailScreenState extends State<InterviewInvitationDetailScreen> {
  late Future<InterviewInvitation> _invitationFuture;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _invitationFuture = _loadInvitation();
  }

  Future<InterviewInvitation> _loadInvitation() {
    return context.read<ApplicantWorkflowService>().getInterviewInvitation(widget.invitationId);
  }

  void _refresh() {
    setState(() {
      _invitationFuture = _loadInvitation();
    });
  }

  Future<void> _accept() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Accept invitation?'),
        content: const Text('This will schedule the interview at the proposed time.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Accept')),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _isSubmitting = true);
    try {
      await context.read<ApplicantWorkflowService>().acceptInterviewInvitation(widget.invitationId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Invitation accepted.')));
      _refresh();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Future<void> _decline() async {
    final reason = await _showDeclineReasonDialog();
    if (reason == null) return;

    setState(() => _isSubmitting = true);
    try {
      await context.read<ApplicantWorkflowService>().declineInterviewInvitation(
            widget.invitationId,
            declineReason: reason,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Invitation declined.')));
      _refresh();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Future<String?> _showDeclineReasonDialog() async {
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Decline invitation'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Reason',
            hintText: 'Tell the interviewer why you cannot attend',
          ),
          minLines: 2,
          maxLines: 4,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              final value = controller.text.trim();
              if (value.isNotEmpty) Navigator.pop(context, value);
            },
            child: const Text('Decline'),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Invitation details'),
        body: SafeArea(
        child: FutureBuilder<InterviewInvitation>(
          future: _invitationFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return ApiErrorMessage(error: snapshot.error!, onRetry: _refresh);
            }
            final invitation = snapshot.data!;
            final application = invitation.application;
            return ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(
                  application?.jobTitle.isNotEmpty == true ? application!.jobTitle : 'Interview invitation',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 6),
                Text(application?.organizationName.isNotEmpty == true ? application!.organizationName : 'Organization not available'),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    Chip(label: Text(titleCaseStatus(invitation.status))),
                    Chip(label: Text(formatDateTime(invitation.proposedDatetime))),
                    Chip(label: Text(titleCaseStatus(invitation.mode))),
                  ],
                ),
                const SizedBox(height: 20),
                _DetailRow(label: 'Interviewer', value: invitation.interviewerName),
                _DetailRow(label: 'Interviewer email', value: invitation.interviewerEmail),
                _DetailRow(label: 'Sent', value: formatDateTime(invitation.sentAt)),
                if (invitation.respondedAt != null)
                  _DetailRow(label: 'Responded', value: formatDateTime(invitation.respondedAt)),
                if (invitation.location.isNotEmpty) _DetailRow(label: 'Location', value: invitation.location),
                if (invitation.declineReason.isNotEmpty)
                  _DetailRow(label: 'Decline reason', value: invitation.declineReason),
                const SizedBox(height: 12),
                if (invitation.meetingLink.isNotEmpty)
                  OutlinedButton.icon(
                    onPressed: () => launchUrlString(invitation.meetingLink),
                    icon: const Icon(Icons.video_call_outlined),
                    label: const Text('Open meeting link'),
                  ),
                if (invitation.calendarLink.isNotEmpty)
                  OutlinedButton.icon(
                    onPressed: () => launchUrlString(invitation.calendarLink),
                    icon: const Icon(Icons.calendar_month_outlined),
                    label: const Text('Open calendar link'),
                  ),
                if (invitation.canRespond) ...[
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _isSubmitting ? null : _decline,
                          icon: const Icon(Icons.close),
                          label: const Text('Decline'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: _isSubmitting ? null : _accept,
                          icon: const Icon(Icons.check),
                          label: const Text('Accept'),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            );
          },
        ),
      ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    if (value.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 2),
          Text(value),
        ],
      ),
    );
  }
}
