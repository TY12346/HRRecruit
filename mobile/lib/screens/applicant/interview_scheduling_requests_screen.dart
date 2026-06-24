import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/applicant_interview.dart';
import '../../services/applicant_workflow_service.dart';
import '../../widgets/app_navigation.dart';
import 'applicant_workflow_widgets.dart';
import 'job_cards.dart';

class InterviewSchedulingRequestsScreen extends StatefulWidget {
  const InterviewSchedulingRequestsScreen({super.key});

  @override
  State<InterviewSchedulingRequestsScreen> createState() => _InterviewSchedulingRequestsScreenState();
}

class _InterviewSchedulingRequestsScreenState extends State<InterviewSchedulingRequestsScreen> {
  late Future<List<InterviewSchedulingRequest>> _requestsFuture;
  int? _bookingRequestId;

  @override
  void initState() {
    super.initState();
    _requestsFuture = _loadRequests();
  }

  Future<List<InterviewSchedulingRequest>> _loadRequests() {
    return context.read<ApplicantWorkflowService>().getInterviewSchedulingRequests();
  }

  void _refresh() {
    setState(() {
      _requestsFuture = _loadRequests();
    });
  }

  Future<void> _bookSlot(InterviewSchedulingRequest request, InterviewerAvailabilitySlot slot) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Book this interview slot?'),
        content: Text('Confirm ${formatDateTime(slot.startDatetime)} for ${request.application?.jobTitle ?? 'this interview'}.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Book slot')),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _bookingRequestId = request.id);
    try {
      await context.read<ApplicantWorkflowService>().bookInterviewSchedulingRequest(
            requestId: request.id,
            slot: slot,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Interview slot booked successfully.')),
      );
      _refresh();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Unable to book slot: $error')),
      );
    } finally {
      if (mounted) setState(() => _bookingRequestId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Schedule interviews'),
        body: SafeArea(
          child: RefreshIndicator(
            onRefresh: () async {
              _refresh();
              await _requestsFuture;
            },
            child: FutureBuilder<List<InterviewSchedulingRequest>>(
              future: _requestsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return ApiErrorMessage(error: snapshot.error!, onRetry: _refresh);
                }
                final requests = snapshot.data ?? [];
                if (requests.isEmpty) {
                  return const ApplicantWorkflowMessage(
                    icon: Icons.event_available_outlined,
                    title: 'No self-scheduling requests yet',
                    message: 'When a recruiter asks you to choose an interview time, the request will appear here.',
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: requests.length,
                  itemBuilder: (context, index) {
                    final request = requests[index];
                    return _SchedulingRequestCard(
                      request: request,
                      isBooking: _bookingRequestId == request.id,
                      onBook: (slot) => _bookSlot(request, slot),
                    );
                  },
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

class _SchedulingRequestCard extends StatelessWidget {
  const _SchedulingRequestCard({
    required this.request,
    required this.isBooking,
    required this.onBook,
  });

  final InterviewSchedulingRequest request;
  final bool isBooking;
  final ValueChanged<InterviewerAvailabilitySlot> onBook;

  @override
  Widget build(BuildContext context) {
    final application = request.application;
    final selectedSlot = request.selectedSlot;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              application?.jobTitle.isNotEmpty == true ? application!.jobTitle : 'Interview scheduling request',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(application?.organizationName.isNotEmpty == true ? application!.organizationName : 'Organization not available'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                Chip(label: Text(titleCaseStatus(request.status))),
                if (request.expiresAt != null) Chip(label: Text('Expires ${formatDateTime(request.expiresAt)}')),
              ],
            ),
            if (request.interviewerName.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('Interviewer: ${request.interviewerName}'),
            ],
            if (request.remark.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('Remark: ${request.remark}'),
            ],
            if (selectedSlot != null) ...[
              const SizedBox(height: 12),
              Text('Selected slot: ${formatDateTime(selectedSlot.startDatetime)}'),
            ],
            if (request.status == 'pending') ...[
              const SizedBox(height: 12),
              Text('Available slots', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              if (request.availableSlots.isEmpty)
                const Text('No available slots at the moment. Please check again later.'),
              ...request.availableSlots.map(
                (slot) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: OutlinedButton.icon(
                    onPressed: isBooking ? null : () => onBook(slot),
                    icon: isBooking
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.event_available_outlined),
                    label: Text('${formatDateTime(slot.startDatetime)} – ${formatDateTime(slot.endDatetime)}'),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
