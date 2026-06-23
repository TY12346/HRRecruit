import 'job_application.dart';

class InterviewInvitation {
  const InterviewInvitation({
    required this.id,
    required this.interviewId,
    required this.interviewStatus,
    required this.application,
    required this.interviewerName,
    required this.interviewerEmail,
    required this.proposedDatetime,
    required this.mode,
    required this.meetingLink,
    required this.location,
    required this.status,
    required this.declineReason,
    required this.calendarLink,
    required this.sentAt,
    required this.respondedAt,
  });

  final int id;
  final int interviewId;
  final String interviewStatus;
  final JobApplication? application;
  final String interviewerName;
  final String interviewerEmail;
  final DateTime? proposedDatetime;
  final String mode;
  final String meetingLink;
  final String location;
  final String status;
  final String declineReason;
  final String calendarLink;
  final DateTime? sentAt;
  final DateTime? respondedAt;

  bool get canRespond => status == 'pending';

  factory InterviewInvitation.fromJson(Map<String, dynamic> json) {
    final interviewer = json['interviewer'];
    return InterviewInvitation(
      id: _asInt(json['id']),
      interviewId: _asInt(json['interview']),
      interviewStatus: json['interview_status'] as String? ?? '',
      application: json['application'] is Map<String, dynamic>
          ? JobApplication.fromJson(json['application'] as Map<String, dynamic>)
          : null,
      interviewerName: interviewer is Map<String, dynamic>
          ? interviewer['full_name'] as String? ?? ''
          : '',
      interviewerEmail: interviewer is Map<String, dynamic>
          ? interviewer['email'] as String? ?? ''
          : '',
      proposedDatetime: _asDateTime(json['proposed_datetime']),
      mode: json['mode'] as String? ?? '',
      meetingLink: json['meeting_link'] as String? ?? '',
      location: json['location'] as String? ?? '',
      status: json['status'] as String? ?? '',
      declineReason: json['decline_reason'] as String? ?? '',
      calendarLink: json['calendar_link'] as String? ?? '',
      sentAt: _asDateTime(json['sent_at']),
      respondedAt: _asDateTime(json['responded_at']),
    );
  }
}

class ApplicantInterview {
  const ApplicantInterview({
    required this.id,
    required this.application,
    required this.interviewerName,
    required this.interviewerEmail,
    required this.scheduledDatetime,
    required this.mode,
    required this.meetingLink,
    required this.location,
    required this.status,
    required this.latestInvitation,
    required this.calendarLink,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final JobApplication? application;
  final String interviewerName;
  final String interviewerEmail;
  final DateTime? scheduledDatetime;
  final String mode;
  final String meetingLink;
  final String location;
  final String status;
  final InterviewInvitation? latestInvitation;
  final String calendarLink;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  bool get isCompleted => status == 'completed';

  factory ApplicantInterview.fromJson(Map<String, dynamic> json) {
    final interviewer = json['interviewer'];
    final latestInvitation = json['latest_invitation'];
    return ApplicantInterview(
      id: _asInt(json['id']),
      application: json['application'] is Map<String, dynamic>
          ? JobApplication.fromJson(json['application'] as Map<String, dynamic>)
          : null,
      interviewerName: interviewer is Map<String, dynamic>
          ? interviewer['full_name'] as String? ?? ''
          : '',
      interviewerEmail: interviewer is Map<String, dynamic>
          ? interviewer['email'] as String? ?? ''
          : '',
      scheduledDatetime: _asDateTime(json['scheduled_datetime']),
      mode: json['mode'] as String? ?? '',
      meetingLink: json['meeting_link'] as String? ?? '',
      location: json['location'] as String? ?? '',
      status: json['status'] as String? ?? '',
      latestInvitation: latestInvitation is Map<String, dynamic>
          ? InterviewInvitation.fromJson({
              ...latestInvitation,
              'id': latestInvitation['id'] ?? 0,
              'interview': json['id'],
              'interview_status': json['status'],
              'application': json['application'],
              'interviewer': json['interviewer'],
              'calendar_link': json['calendar_link'],
            })
          : null,
      calendarLink: json['calendar_link'] as String? ?? '',
      createdAt: _asDateTime(json['created_at']),
      updatedAt: _asDateTime(json['updated_at']),
    );
  }
}

int _asInt(Object? value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? 0;
}

DateTime? _asDateTime(Object? value) {
  if (value == null) return null;
  return DateTime.tryParse(value.toString());
}

class InterviewerAvailabilitySlot {
  const InterviewerAvailabilitySlot({
    required this.id,
    required this.startDatetime,
    required this.endDatetime,
    required this.status,
  });

  final int id;
  final DateTime? startDatetime;
  final DateTime? endDatetime;
  final String status;

  factory InterviewerAvailabilitySlot.fromJson(Map<String, dynamic> json) {
    return InterviewerAvailabilitySlot(
      id: _asInt(json['id']),
      startDatetime: _asDateTime(json['start_datetime']),
      endDatetime: _asDateTime(json['end_datetime']),
      status: json['status'] as String? ?? '',
    );
  }
}

class InterviewSchedulingRequest {
  const InterviewSchedulingRequest({
    required this.id,
    required this.application,
    required this.interviewerName,
    required this.interviewerEmail,
    required this.remark,
    required this.status,
    required this.expiresAt,
    required this.selectedSlot,
    required this.interviewId,
    required this.availableSlots,
    required this.createdAt,
  });

  final int id;
  final JobApplication? application;
  final String interviewerName;
  final String interviewerEmail;
  final String remark;
  final String status;
  final DateTime? expiresAt;
  final InterviewerAvailabilitySlot? selectedSlot;
  final int interviewId;
  final List<InterviewerAvailabilitySlot> availableSlots;
  final DateTime? createdAt;

  bool get canBook => status == 'pending' && availableSlots.isNotEmpty;

  factory InterviewSchedulingRequest.fromJson(Map<String, dynamic> json) {
    final interviewer = json['interviewer'];
    final selectedSlot = json['selected_slot'];
    final availableSlots = json['available_slots'];
    return InterviewSchedulingRequest(
      id: _asInt(json['id']),
      application: json['application'] is Map<String, dynamic>
          ? JobApplication.fromJson(json['application'] as Map<String, dynamic>)
          : null,
      interviewerName: interviewer is Map<String, dynamic>
          ? interviewer['full_name'] as String? ?? ''
          : '',
      interviewerEmail: interviewer is Map<String, dynamic>
          ? interviewer['email'] as String? ?? ''
          : '',
      remark: json['remark'] as String? ?? '',
      status: json['status'] as String? ?? '',
      expiresAt: _asDateTime(json['expires_at']),
      selectedSlot: selectedSlot is Map<String, dynamic>
          ? InterviewerAvailabilitySlot.fromJson(selectedSlot)
          : null,
      interviewId: _asInt(json['interview']),
      availableSlots: availableSlots is List
          ? availableSlots
              .whereType<Map<String, dynamic>>()
              .map(InterviewerAvailabilitySlot.fromJson)
              .toList()
          : const [],
      createdAt: _asDateTime(json['created_at']),
    );
  }
}
