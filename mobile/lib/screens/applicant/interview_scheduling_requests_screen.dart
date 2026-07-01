import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/applicant_interview.dart';
import '../../services/applicant_workflow_service.dart';
import '../../widgets/app_navigation.dart';
import '../auth_form_helpers.dart';
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

  Future<void> _openSlotSelection(InterviewSchedulingRequest request) async {
    final booked = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => InterviewSlotSelectionScreen(request: request),
      ),
    );
    if (booked == true) _refresh();
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
                      onSelectSlot: () => _openSlotSelection(request),
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
    required this.onSelectSlot,
  });

  final InterviewSchedulingRequest request;
  final bool isBooking;
  final VoidCallback onSelectSlot;

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
              Text('Stage/remark: ${request.remark}'),
            ],
            if (selectedSlot != null) ...[
              const SizedBox(height: 12),
              Text('Selected slot: ${formatDateTime(selectedSlot.startDatetime)}'),
            ],
            if (request.status == 'pending') ...[
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: isBooking ? null : onSelectSlot,
                icon: const Icon(Icons.event_available_outlined),
                label: const Text('Select interview slot'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class InterviewSlotSelectionScreen extends StatefulWidget {
  const InterviewSlotSelectionScreen({super.key, required this.request});

  final InterviewSchedulingRequest request;

  @override
  State<InterviewSlotSelectionScreen> createState() => _InterviewSlotSelectionScreenState();
}

class _InterviewSlotSelectionScreenState extends State<InterviewSlotSelectionScreen> {
  late Future<List<InterviewAvailableDate>> _datesFuture;
  Future<List<InterviewerAvailabilitySlot>>? _slotsFuture;
  InterviewAvailableDate? _selectedDate;
  InterviewerAvailabilitySlot? _selectedSlot;
  int _step = 0;
  bool _isBooking = false;

  int get _applicationId => widget.request.application?.id ?? 0;

  @override
  void initState() {
    super.initState();
    _datesFuture = _loadDates();
  }

  Future<List<InterviewAvailableDate>> _loadDates() {
    return context.read<ApplicantWorkflowService>().getInterviewAvailableDates(_applicationId);
  }

  Future<List<InterviewerAvailabilitySlot>> _loadSlots(String dateKey) {
    return context.read<ApplicantWorkflowService>().getInterviewAvailableSlots(
          applicationId: _applicationId,
          date: dateKey,
        );
  }

  void _goToTimeStep() {
    final selectedDate = _selectedDate;
    if (selectedDate == null) return;
    setState(() {
      _step = 1;
      _selectedSlot = null;
      _slotsFuture = _loadSlots(selectedDate.dateKey);
    });
  }

  void _goToConfirmationStep() {
    if (_selectedSlot == null) return;
    setState(() => _step = 2);
  }

  Future<void> _confirmBooking() async {
    final slot = _selectedSlot;
    if (slot == null) return;
    setState(() => _isBooking = true);
    try {
      await context.read<ApplicantWorkflowService>().bookInterviewSchedulingRequest(
            requestId: widget.request.id,
            applicationId: _applicationId,
            slot: slot,
            mode: slot.mode.isEmpty ? 'online' : slot.mode,
            meetingLink: slot.meetingLink.isEmpty ? 'https://meet.example.com/hrrecruit-interview' : slot.meetingLink,
            location: slot.location,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Interview slot booked successfully.')),
      );
      Navigator.of(context).pop(true);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Unable to book slot. ${readableApiError(error)}')),
      );
      setState(() {
        _step = 1;
        _selectedSlot = null;
        if (_selectedDate != null) _slotsFuture = _loadSlots(_selectedDate!.dateKey);
      });
    } finally {
      if (mounted) setState(() => _isBooking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.request.application?.jobTitle.isNotEmpty == true
        ? widget.request.application!.jobTitle
        : 'Interview';
    return Scaffold(
      appBar: appScreenAppBar(context, title: _step == 0 ? 'Select Interview Date' : _step == 1 ? 'Select Interview Time' : 'Confirm Interview Slot'),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 4),
              Text(
                widget.request.remark.isNotEmpty ? widget.request.remark : 'Interview stage',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              Expanded(child: _buildCurrentStep()),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCurrentStep() {
    if (_step == 0) return _buildDateStep();
    if (_step == 1) return _buildTimeStep();
    return _buildConfirmationStep();
  }

  Widget _buildDateStep() {
    return FutureBuilder<List<InterviewAvailableDate>>(
      future: _datesFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return ApiErrorMessage(error: snapshot.error!, onRetry: () => setState(() => _datesFuture = _loadDates()));
        }
        final dates = snapshot.data ?? [];
        if (dates.isEmpty) {
          return const ApplicantWorkflowMessage(
            icon: Icons.event_busy_outlined,
            title: 'No dates available',
            message: 'There are no interview dates available right now. Please check again later.',
          );
        }
        return Column(
          children: [
            Expanded(
              child: ListView.separated(
                itemCount: dates.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final availableDate = dates[index];
                  final isSelected = availableDate.dateKey == _selectedDate?.dateKey;
                  return Card(
                    color: isSelected ? Theme.of(context).colorScheme.primaryContainer : null,
                    child: ListTile(
                      onTap: () => setState(() => _selectedDate = availableDate),
                      leading: const Icon(Icons.calendar_month_outlined),
                      title: Text('${availableDate.dayOfWeek}, ${formatDate(availableDate.date)}'),
                      subtitle: Text('${availableDate.availableSlotCount} slots available'),
                      trailing: isSelected ? const Icon(Icons.check_circle) : null,
                    ),
                  );
                },
              ),
            ),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _selectedDate == null ? null : _goToTimeStep,
                child: const Text('Next'),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildTimeStep() {
    final selectedDate = _selectedDate;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (selectedDate != null) ...[
          Text('Selected date', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 4),
          Text('${selectedDate.dayOfWeek}, ${formatDate(selectedDate.date)}'),
          const SizedBox(height: 12),
        ],
        Expanded(
          child: FutureBuilder<List<InterviewerAvailabilitySlot>>(
            future: _slotsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ApiErrorMessage(
                  error: snapshot.error!,
                  onRetry: selectedDate == null ? () {} : () => setState(() => _slotsFuture = _loadSlots(selectedDate.dateKey)),
                );
              }
              final slots = snapshot.data ?? [];
              if (slots.isEmpty) {
                return const ApplicantWorkflowMessage(
                  icon: Icons.schedule_outlined,
                  title: 'No times available',
                  message: 'This date no longer has available slots. Please go back and choose another date.',
                );
              }
              return ListView.separated(
                itemCount: slots.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final slot = slots[index];
                  final isSelected = slot.id == _selectedSlot?.id;
                  return Card(
                    color: isSelected ? Theme.of(context).colorScheme.primaryContainer : null,
                    child: ListTile(
                      onTap: () => setState(() => _selectedSlot = slot),
                      leading: const Icon(Icons.schedule_outlined),
                      title: Text('${_formatTime(slot.startDatetime)} - ${_formatTime(slot.endDatetime)}'),
                      subtitle: Text(slot.mode.isEmpty ? 'Interview mode not specified' : titleCaseStatus(slot.mode)),
                      trailing: isSelected ? const Icon(Icons.check_circle) : null,
                    ),
                  );
                },
              );
            },
          ),
        ),
        Row(
          children: [
            Expanded(child: OutlinedButton(onPressed: () => setState(() => _step = 0), child: const Text('Back'))),
            const SizedBox(width: 12),
            Expanded(child: FilledButton(onPressed: _selectedSlot == null ? null : _goToConfirmationStep, child: const Text('Continue'))),
          ],
        ),
      ],
    );
  }

  Widget _buildConfirmationStep() {
    final slot = _selectedSlot;
    final application = widget.request.application;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _SummaryRow(label: 'Job title', value: application?.jobTitle ?? 'Interview'),
                _SummaryRow(label: 'Interview date', value: formatDate(slot?.startDatetime)),
                _SummaryRow(label: 'Interview time', value: '${_formatTime(slot?.startDatetime)} - ${_formatTime(slot?.endDatetime)}'),
                _SummaryRow(label: 'Mode', value: slot?.mode.isNotEmpty == true ? titleCaseStatus(slot!.mode) : 'Not specified'),
                _SummaryRow(label: 'Interviewer', value: _interviewerSummary(slot)),
                if (slot?.meetingLink.isNotEmpty == true) _SummaryRow(label: 'Meeting link', value: slot!.meetingLink),
                if (slot?.location.isNotEmpty == true) _SummaryRow(label: 'Location', value: slot!.location),
              ],
            ),
          ),
        ),
        const Spacer(),
        Row(
          children: [
            Expanded(child: OutlinedButton(onPressed: _isBooking ? null : () => setState(() => _step = 1), child: const Text('Back'))),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton(
                onPressed: _isBooking ? null : _confirmBooking,
                child: _isBooking
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Confirm Slot'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  String _formatTime(DateTime? value) {
    if (value == null) return 'Not available';
    final local = value.toLocal();
    final hour = local.hour % 12 == 0 ? 12 : local.hour % 12;
    final minute = local.minute.toString().padLeft(2, '0');
    final period = local.hour >= 12 ? 'PM' : 'AM';
    return '$hour:$minute $period';
  }

  String _interviewerSummary(InterviewerAvailabilitySlot? slot) {
    if (slot == null) return widget.request.interviewerName.isEmpty ? 'Not available' : widget.request.interviewerName;
    if (slot.interviewerNames.isNotEmpty) return slot.interviewerNames.join(', ');
    return widget.request.interviewerName.isEmpty ? 'Not available' : widget.request.interviewerName;
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelMedium),
          const SizedBox(height: 2),
          Text(value),
        ],
      ),
    );
  }
}
