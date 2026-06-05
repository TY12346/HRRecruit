class ApplicantProfile {
  const ApplicantProfile({
    required this.id,
    required this.email,
    required this.fullName,
    required this.phoneNumber,
    required this.role,
    required this.linkedinUrl,
    required this.personalSummary,
    this.resumeFile,
  });

  final int id;
  final String email;
  final String fullName;
  final String phoneNumber;
  final String role;
  final String linkedinUrl;
  final String personalSummary;
  final String? resumeFile;

  factory ApplicantProfile.fromJson(Map<String, dynamic> json) {
    return ApplicantProfile(
      id: json['id'] as int,
      email: json['email'] as String? ?? '',
      fullName: json['full_name'] as String? ?? '',
      phoneNumber: json['phone_number'] as String? ?? '',
      role: json['role'] as String? ?? '',
      linkedinUrl: json['linkedin_url'] as String? ?? '',
      personalSummary: json['personal_summary'] as String? ?? '',
      resumeFile: json['resume_file'] as String?,
    );
  }
}
