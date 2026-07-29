class JobApplication {
  const JobApplication({
    required this.id,
    required this.jobId,
    required this.jobTitle,
    required this.organizationName,
    required this.status,
    required this.recruiterRemark,
    required this.finalScore,
    required this.resumeTitle,
    required this.resumeUrl,
    required this.appliedAt,
    required this.updatedAt,
  });

  final String id;
  final String jobId;
  final String jobTitle;
  final String organizationName;
  final String status;
  final String recruiterRemark;
  final double? finalScore;
  final String resumeTitle;
  final String? resumeUrl;
  final DateTime? appliedAt;
  final DateTime? updatedAt;

  bool get canWithdraw => status == 'under_review';

  factory JobApplication.fromJson(Map<String, dynamic> json) {
    return JobApplication(
      id: json['id']?.toString() ?? '',
      jobId: json['job']?.toString() ?? '',
      jobTitle: json['job_title'] as String? ?? '',
      organizationName: json['organization_name'] as String? ?? '',
      status: json['status'] as String? ?? '',
      recruiterRemark: json['recruiter_remark'] as String? ?? '',
      finalScore: _asNullableDouble(json['final_score']),
      resumeTitle: _resumeValue(json, 'title'),
      resumeUrl: _nullableResumeValue(json, 'resume_url'),
      appliedAt: _asDateTime(json['applied_at']),
      updatedAt: _asDateTime(json['updated_at']),
    );
  }
}

String _resumeValue(Map<String, dynamic> json, String key) {
  final resume = json['selected_resume'];
  if (resume is! Map<String, dynamic>) return '';
  return resume[key] as String? ?? '';
}

String? _nullableResumeValue(Map<String, dynamic> json, String key) {
  final value = _resumeValue(json, key).trim();
  return value.isEmpty ? null : value;
}

class ApplicationStageHistory {
  const ApplicationStageHistory({
    required this.id,
    required this.fromStage,
    required this.toStage,
    required this.changedByName,
    required this.note,
    required this.changedAt,
  });

  final String id;
  final String fromStage;
  final String toStage;
  final String changedByName;
  final String note;
  final DateTime? changedAt;

  factory ApplicationStageHistory.fromJson(Map<String, dynamic> json) {
    return ApplicationStageHistory(
      id: json['id']?.toString() ?? '',
      fromStage: json['from_stage'] as String? ?? '',
      toStage: json['to_stage'] as String? ?? '',
      changedByName: json['changed_by_name'] as String? ?? 'System',
      note: json['note'] as String? ?? '',
      changedAt: _asDateTime(json['changed_at']),
    );
  }
}

int _asInt(Object? value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? 0;
}

double? _asNullableDouble(Object? value) {
  if (value == null) return null;
  if (value is num) return value.toDouble();
  return double.tryParse(value.toString());
}

DateTime? _asDateTime(Object? value) {
  if (value == null) return null;
  return DateTime.tryParse(value.toString());
}
