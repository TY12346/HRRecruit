import '../api/api_client.dart';
import '../models/job_application.dart';
import '../models/job_posting.dart';

class JobDiscoveryService {
  const JobDiscoveryService(this._apiClient);

  final ApiClient _apiClient;

  Future<List<JobPosting>> searchJobs({
    String? search,
    String? location,
    String? employmentType,
  }) async {
    final response = await _apiClient.dio.get<List<dynamic>>(
      'jobs/',
      queryParameters: {
        if (search != null && search.trim().isNotEmpty) 'search': search.trim(),
        if (location != null && location.trim().isNotEmpty) 'location': location.trim(),
        if (employmentType != null && employmentType.trim().isNotEmpty)
          'employment_type': employmentType.trim(),
      },
    );
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(JobPosting.fromJson)
        .toList();
  }

  Future<JobPosting> getJob(int jobId) async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>('jobs/$jobId/');
    return JobPosting.fromJson(response.data!);
  }

  Future<List<JobPosting>> getSavedJobs() async {
    final response = await _apiClient.dio.get<List<dynamic>>('jobs/saved/');
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(JobPosting.fromJson)
        .toList();
  }

  Future<void> saveJob(int jobId) async {
    await _apiClient.dio.post<Map<String, dynamic>>('jobs/$jobId/save/');
  }

  Future<void> unsaveJob(int jobId) async {
    await _apiClient.dio.delete<void>('jobs/$jobId/save/');
  }

  Future<JobApplication> applyForJob(int jobId, {required int resumeId}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'jobs/$jobId/apply/',
      data: {'resume_id': resumeId},
      options: _apiClient.longRunningRequestOptions(),
    );
    return JobApplication.fromJson(response.data!);
  }

  Future<JobApplication> withdrawApplication(int jobId) async {
    final response = await _apiClient.dio.delete<Map<String, dynamic>>('jobs/$jobId/apply/');
    return JobApplication.fromJson(response.data!);
  }

  Future<List<JobApplication>> getApplications() async {
    final response = await _apiClient.dio.get<List<dynamic>>('applications/');
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(JobApplication.fromJson)
        .toList();
  }

  Future<JobApplication> getApplication(int applicationId) async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>('applications/$applicationId/');
    return JobApplication.fromJson(response.data!);
  }

  Future<List<ApplicationStageHistory>> getApplicationHistory(int applicationId) async {
    final response = await _apiClient.dio.get<List<dynamic>>(
      'applications/$applicationId/status-history/',
    );
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(ApplicationStageHistory.fromJson)
        .toList();
  }
}
