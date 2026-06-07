class JobApplication {
  const JobApplication({
    required this.id,
    required this.jobId,
    required this.jobTitle,
    required this.organizationName,
    required this.status,
    required this.recruiterRemark,
    required this.finalScore,
    required this.appliedAt,
    required this.updatedAt,
  });

  final int id;
  final int jobId;
  final String jobTitle;
  final String organizationName;
  final String status;
  final String recruiterRemark;
  final double? finalScore;
  final DateTime? appliedAt;
  final DateTime? updatedAt;

  bool get canWithdraw => status == 'submitted' || status == 'screened';

  factory JobApplication.fromJson(Map<String, dynamic> json) {
    return JobApplication(
      id: _asInt(json['id']),
      jobId: _asInt(json['job']),
      jobTitle: json['job_title'] as String? ?? '',
      organizationName: json['organization_name'] as String? ?? '',
      status: json['status'] as String? ?? '',
      recruiterRemark: json['recruiter_remark'] as String? ?? '',
      finalScore: _asNullableDouble(json['final_score']),
      appliedAt: _asDateTime(json['applied_at']),
      updatedAt: _asDateTime(json['updated_at']),
    );
  }
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

  final int id;
  final String fromStage;
  final String toStage;
  final String changedByName;
  final String note;
  final DateTime? changedAt;

  factory ApplicationStageHistory.fromJson(Map<String, dynamic> json) {
    return ApplicationStageHistory(
      id: _asInt(json['id']),
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
