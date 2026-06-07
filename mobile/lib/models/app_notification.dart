class AppNotification {
  const AppNotification({
    required this.id,
    required this.notificationType,
    required this.title,
    required this.message,
    required this.relatedEntityType,
    required this.relatedEntityId,
    required this.isRead,
    required this.createdAt,
  });

  final int id;
  final String notificationType;
  final String title;
  final String message;
  final String relatedEntityType;
  final int? relatedEntityId;
  final bool isRead;
  final DateTime? createdAt;

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: _asInt(json['id']),
      notificationType: json['notification_type'] as String? ?? '',
      title: json['title'] as String? ?? '',
      message: json['message'] as String? ?? '',
      relatedEntityType: json['related_entity_type'] as String? ?? '',
      relatedEntityId: json['related_entity_id'] == null ? null : _asInt(json['related_entity_id']),
      isRead: json['is_read'] == true,
      createdAt: _asDateTime(json['created_at']),
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
