import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/app_notification.dart';
import '../../services/applicant_workflow_service.dart';
import '../auth_form_helpers.dart';
import 'applicant_workflow_widgets.dart';
import 'job_cards.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  late Future<List<AppNotification>> _notificationsFuture;
  int? _busyNotificationId;
  bool _isMarkingAll = false;

  @override
  void initState() {
    super.initState();
    _notificationsFuture = _loadNotifications();
  }

  Future<List<AppNotification>> _loadNotifications() {
    return context.read<ApplicantWorkflowService>().getNotifications();
  }

  void _refresh() {
    setState(() {
      _notificationsFuture = _loadNotifications();
    });
  }

  Future<void> _markRead(AppNotification notification) async {
    if (notification.isRead) return;
    setState(() => _busyNotificationId = notification.id);
    try {
      await context.read<ApplicantWorkflowService>().markNotificationRead(notification.id);
      if (!mounted) return;
      _refresh();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) setState(() => _busyNotificationId = null);
    }
  }

  Future<void> _markAllRead() async {
    setState(() => _isMarkingAll = true);
    try {
      final updated = await context.read<ApplicantWorkflowService>().markAllNotificationsRead();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Marked $updated notification${updated == 1 ? '' : 's'} as read.')),
      );
      _refresh();
    } catch (error) {
      if (!mounted) return;
      showErrorSnackBar(context, error);
    } finally {
      if (mounted) setState(() => _isMarkingAll = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          TextButton(
            onPressed: _isMarkingAll ? null : _markAllRead,
            child: Text(_isMarkingAll ? 'Marking...' : 'Read all'),
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            _refresh();
            await _notificationsFuture;
          },
          child: FutureBuilder<List<AppNotification>>(
            future: _notificationsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ApiErrorMessage(error: snapshot.error!, onRetry: _refresh);
              }
              final notifications = snapshot.data ?? [];
              if (notifications.isEmpty) {
                return const ApplicantWorkflowMessage(
                  icon: Icons.notifications_none,
                  title: 'No notifications yet',
                  message: 'Application, interview, and offer updates will appear here.',
                );
              }
              return ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: notifications.length,
                itemBuilder: (context, index) {
                  final notification = notifications[index];
                  return Card(
                    color: notification.isRead ? null : Theme.of(context).colorScheme.primaryContainer,
                    child: ListTile(
                      leading: Icon(notification.isRead ? Icons.notifications_none : Icons.notifications),
                      title: Text(notification.title),
                      subtitle: Text(
                        '${notification.message}\n${formatDateTime(notification.createdAt)}',
                      ),
                      isThreeLine: true,
                      trailing: notification.isRead
                          ? const Icon(Icons.done)
                          : _busyNotificationId == notification.id
                              ? const SizedBox(
                                  width: 24,
                                  height: 24,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : TextButton(
                                  onPressed: () => _markRead(notification),
                                  child: const Text('Read'),
                                ),
                      onTap: () => _markRead(notification),
                    ),
                  );
                },
              );
            },
          ),
        ),
      ),
    );
  }
}
