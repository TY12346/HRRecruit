import 'job_application.dart';

class JobOffer {
  const JobOffer({
    required this.id,
    required this.application,
    required this.offerLetterUrl,
    required this.offerMessage,
    required this.offerStatus,
    required this.respondDeadline,
    required this.sentAt,
    required this.respondedAt,
  });

  final int id;
  final JobApplication? application;
  final String offerLetterUrl;
  final String offerMessage;
  final String offerStatus;
  final DateTime? respondDeadline;
  final DateTime? sentAt;
  final DateTime? respondedAt;

  bool get canRespond => offerStatus == 'sent';

  factory JobOffer.fromJson(Map<String, dynamic> json) {
    return JobOffer(
      id: _asInt(json['id']),
      application: json['application'] is Map<String, dynamic>
          ? JobApplication.fromJson(json['application'] as Map<String, dynamic>)
          : null,
      offerLetterUrl: json['offer_letter_url'] as String? ?? '',
      offerMessage: json['offer_message'] as String? ?? '',
      offerStatus: json['offer_status'] as String? ?? '',
      respondDeadline: _asDateTime(json['respond_deadline']),
      sentAt: _asDateTime(json['sent_at']),
      respondedAt: _asDateTime(json['responded_at']),
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
