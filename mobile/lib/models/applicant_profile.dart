class ApplicantExperience {
  const ApplicantExperience({
    this.experienceId,
    required this.jobTitle,
    required this.employmentType,
    required this.companyName,
    required this.startDate,
    required this.location,
  });

  final int? experienceId;
  final String jobTitle;
  final String employmentType;
  final String companyName;
  final String startDate;
  final String location;

  factory ApplicantExperience.fromJson(Map<String, dynamic> json) {
    return ApplicantExperience(
      experienceId: json['experience_id'] as int?,
      jobTitle: json['job_title'] as String? ?? '',
      employmentType: json['employment_type'] as String? ?? '',
      companyName: json['company_name'] as String? ?? '',
      startDate: json['start_date'] as String? ?? '',
      location: json['location'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'job_title': jobTitle,
        'employment_type': employmentType,
        'company_name': companyName,
        'start_date': startDate.isEmpty ? null : startDate,
        'location': location,
      };
}

class ApplicantEducation {
  const ApplicantEducation({
    this.educationId,
    required this.schoolName,
    required this.degreeName,
    required this.fieldOfStudy,
    required this.startDate,
    required this.endDate,
    required this.grade,
  });

  final int? educationId;
  final String schoolName;
  final String degreeName;
  final String fieldOfStudy;
  final String startDate;
  final String endDate;
  final String grade;

  factory ApplicantEducation.fromJson(Map<String, dynamic> json) {
    return ApplicantEducation(
      educationId: json['education_id'] as int?,
      schoolName: json['school_name'] as String? ?? '',
      degreeName: json['degree_name'] as String? ?? '',
      fieldOfStudy: json['field_of_study'] as String? ?? '',
      startDate: json['start_date'] as String? ?? '',
      endDate: json['end_date'] as String? ?? '',
      grade: json['grade'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'school_name': schoolName,
        'degree_name': degreeName,
        'field_of_study': fieldOfStudy,
        'start_date': startDate.isEmpty ? null : startDate,
        'end_date': endDate.isEmpty ? null : endDate,
        'grade': grade,
      };
}

class ApplicantSkill {
  const ApplicantSkill({this.skillId, required this.skillName});

  final int? skillId;
  final String skillName;

  factory ApplicantSkill.fromJson(Map<String, dynamic> json) {
    return ApplicantSkill(
      skillId: json['skill_id'] as int?,
      skillName: json['skill_name'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {'skill_name': skillName};
}

class ApplicantProfile {
  const ApplicantProfile({
    required this.id,
    required this.email,
    required this.fullName,
    required this.phoneNumber,
    required this.role,
    required this.linkedinUrl,
    required this.personalSummary,
    required this.experiences,
    required this.educations,
    required this.skills,
    this.resumeFile,
  });

  final int id;
  final String email;
  final String fullName;
  final String phoneNumber;
  final String role;
  final String linkedinUrl;
  final String personalSummary;
  final List<ApplicantExperience> experiences;
  final List<ApplicantEducation> educations;
  final List<ApplicantSkill> skills;
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
      experiences: _listFromJson(json['experiences'], ApplicantExperience.fromJson),
      educations: _listFromJson(json['educations'], ApplicantEducation.fromJson),
      skills: _listFromJson(json['skills'], ApplicantSkill.fromJson),
      resumeFile: json['resume_file'] as String?,
    );
  }

  static List<T> _listFromJson<T>(
    Object? value,
    T Function(Map<String, dynamic>) mapper,
  ) {
    if (value is! List) return const [];
    return value
        .whereType<Map<String, dynamic>>()
        .map(mapper)
        .toList(growable: true);
  }
}
