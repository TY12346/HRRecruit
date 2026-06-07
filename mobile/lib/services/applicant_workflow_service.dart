import '../api/api_client.dart';
import '../models/app_notification.dart';
import '../models/applicant_interview.dart';
import '../models/job_offer.dart';

class ApplicantWorkflowService {
  const ApplicantWorkflowService(this._apiClient);

  final ApiClient _apiClient;

  Future<List<InterviewInvitation>> getInterviewInvitations() async {
    final response = await _apiClient.dio.get<List<dynamic>>('interview-invitations/');
    return (response.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(InterviewInvitation.fromJson)
        .toList();
  }

  Future<InterviewInvitation> getInterviewInvitation(int invitationId) async {
    final invitations = await getInterviewInvitations();
    return invitations.firstWhere(
      (invitation) => invitation.id == invitationId,
      orElse: () => throw Exception('Interview invitation not found.'),
    );
  }

  Future<InterviewInvitation> acceptInterviewInvitation(int invitationId) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'interview-invitations/$invitationId/accept/',
    );
    return InterviewInvitation.fromJson(response.data!);
  }

  Future<InterviewInvitation> declineInterviewInvitation(
    int invitationId, {
    required String declineReason,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      'interview-invitations/$invitationId/decline/',
      data: {'decline_reason': declineReason},
    );
    return InterviewInvitation.fromJson(response.data!);
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
