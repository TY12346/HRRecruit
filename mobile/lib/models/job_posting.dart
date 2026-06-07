class JobRequirement {
  const JobRequirement({
    required this.id,
    required this.requirementType,
    required this.description,
    required this.weightScore,
    required this.minimumThreshold,
  });

  final int id;
  final String requirementType;
  final String description;
  final double weightScore;
  final double minimumThreshold;

  factory JobRequirement.fromJson(Map<String, dynamic> json) {
    return JobRequirement(
      id: _asInt(json['id']),
      requirementType: json['requirement_type'] as String? ?? '',
      description: json['description'] as String? ?? '',
      weightScore: _asDouble(json['weight_score']),
      minimumThreshold: _asDouble(json['minimum_threshold']),
    );
  }
}

class JobPosting {
  const JobPosting({
    required this.id,
    required this.organizationName,
    required this.recruiterName,
    required this.title,
    required this.description,
    required this.employmentType,
    required this.approximateSalary,
    required this.location,
    required this.status,
    required this.requirements,
    required this.isSaved,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final String organizationName;
  final String recruiterName;
  final String title;
  final String description;
  final String employmentType;
  final double approximateSalary;
  final String location;
  final String status;
  final List<JobRequirement> requirements;
  final bool isSaved;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  factory JobPosting.fromJson(Map<String, dynamic> json) {
    final requirements = (json['requirements'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .map(JobRequirement.fromJson)
        .toList();

    return JobPosting(
      id: _asInt(json['id']),
      organizationName: json['organization_name'] as String? ?? '',
      recruiterName: json['recruiter_name'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      employmentType: json['employment_type'] as String? ?? '',
      approximateSalary: _asDouble(json['approximate_salary']),
      location: json['location'] as String? ?? '',
      status: json['status'] as String? ?? '',
      requirements: requirements,
      isSaved: json['is_saved'] as bool? ?? false,
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

double _asDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}

DateTime? _asDateTime(Object? value) {
  if (value == null) return null;
  return DateTime.tryParse(value.toString());
}
