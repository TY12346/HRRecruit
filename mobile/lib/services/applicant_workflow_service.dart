import '../api/api_client.dart';
import '../models/app_notification.dart';
import '../models/applicant_interview.dart';
import '../models/job_offer.dart';

class ApplicantWorkflowService {
  const ApplicantWorkflowService(this._apiClient);

  final ApiClient _apiClient;

  Future<List<InterviewSchedulingRequest>> getInterviewSchedulingRequests() async {
    final response = await _apiClient.dio.get<List<dynamic>>('interviews/scheduling-requests/');
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(InterviewSchedulingRequest.fromJson)
        .toList();
  }

  Future<InterviewSchedulingRequest> getInterviewSchedulingRequest(int requestId) async {
    final requests = await getInterviewSchedulingRequests();
    return requests.firstWhere(
      (request) => request.id == requestId,
      orElse: () => throw Exception('Interview scheduling request not found.'),
    );
  }

  Future<InterviewSchedulingRequest> bookInterviewSchedulingRequest({
    required int requestId,
    required int slotId,
    String mode = 'online',
    String meetingLink = 'https://meet.example.com/hrrecruit-interview',
    String location = '',
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'interviews/scheduling-requests/$requestId/book/',
      data: {
        'slot_id': slotId,
        'mode': mode,
        'meeting_link': meetingLink,
        'location': location,
      },
    );
    return InterviewSchedulingRequest.fromJson(response.data!);
  }

  Future<List<InterviewSchedulingRequest>> getInterviewSchedulingRequests() async {
    final response = await _apiClient.dio.get<List<dynamic>>('interviews/scheduling-requests/');
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(InterviewSchedulingRequest.fromJson)
        .toList();
  }

  Future<InterviewSchedulingRequest> getInterviewSchedulingRequest(int requestId) async {
    final requests = await getInterviewSchedulingRequests();
    return requests.firstWhere(
      (request) => request.id == requestId,
      orElse: () => throw Exception('Interview scheduling request not found.'),
    );
  }

  Future<InterviewSchedulingRequest> bookInterviewSchedulingRequest({
    required int requestId,
    required int slotId,
    String mode = 'online',
    String meetingLink = 'https://meet.example.com/hrrecruit-interview',
    String location = '',
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'interviews/scheduling-requests/$requestId/book/',
      data: {
        'slot_id': slotId,
        'mode': mode,
        'meeting_link': meetingLink,
        'location': location,
      },
    );
    return InterviewSchedulingRequest.fromJson(response.data!);
  }

  Future<List<ApplicantInterview>> getInterviews() async {
    final response = await _apiClient.dio.get<List<dynamic>>('interviews/');
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(ApplicantInterview.fromJson)
        .toList();
  }

  Future<List<JobOffer>> getJobOffers() async {
    final response = await _apiClient.dio.get<List<dynamic>>('job-offers/');
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(JobOffer.fromJson)
        .toList();
  }

  Future<JobOffer> acceptJobOffer(int offerId) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'job-offers/$offerId/accept/',
    );
    return JobOffer.fromJson(response.data!);
  }

  Future<JobOffer> declineJobOffer(int offerId, {String reason = ''}) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'job-offers/$offerId/decline/',
      data: {'reason': reason},
    );
    return JobOffer.fromJson(response.data!);
  }

  Future<List<AppNotification>> getNotifications() async {
    final response = await _apiClient.dio.get<List<dynamic>>('notifications/');
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(AppNotification.fromJson)
        .toList();
  }

  Future<AppNotification> markNotificationRead(int notificationId) async {
    final response = await _apiClient.dio.patch<Map<String, dynamic>>(
      'notifications/$notificationId/read/',
    );
    return AppNotification.fromJson(response.data!);
  }

  Future<int> markAllNotificationsRead() async {
    final response = await _apiClient.dio.patch<Map<String, dynamic>>('notifications/read-all/');
    final count = response.data?['updated_count'];
    if (count is num) return count.toInt();
    return int.tryParse(count?.toString() ?? '') ?? 0;
  }
}
