class EmployerInvite {
  const EmployerInvite(
      {required this.id,
      required this.jobId,
      required this.jobTitle,
      required this.organizationName,
      required this.response,
      required this.createdAt});
  final String id;
  final String jobId;
  final String jobTitle;
  final String organizationName;
  final String response;
  final DateTime createdAt;
  factory EmployerInvite.fromJson(Map<String, dynamic> json) => EmployerInvite(
      id: json['id']?.toString() ?? '',
      jobId: json['job']?.toString() ?? '',
      jobTitle: json['job_title'] as String? ?? 'Job',
      organizationName: json['organization_name'] as String? ?? '',
      response: json['response'] as String? ?? 'no_response',
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ??
          DateTime.now());
}
