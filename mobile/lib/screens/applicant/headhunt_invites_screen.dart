import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/employer_invite.dart';
import '../../services/job_discovery_service.dart';
import '../../widgets/app_navigation.dart';
import '../auth_form_helpers.dart';
import 'applicant_workflow_widgets.dart';

class HeadhuntInvitesScreen extends StatefulWidget {
  const HeadhuntInvitesScreen({super.key});

  @override
  State<HeadhuntInvitesScreen> createState() => _HeadhuntInvitesScreenState();
}

class _HeadhuntInvitesScreenState extends State<HeadhuntInvitesScreen> {
  late Future<List<EmployerInvite>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<EmployerInvite>> _load() {
    return context.read<JobDiscoveryService>().getEmployerInvites();
  }

  void _refresh() {
    setState(() => _future = _load());
  }

  Future<void> _decline(EmployerInvite invite) async {
    try {
      await context.read<JobDiscoveryService>().declineEmployerInvite(invite.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invitation declined.')),
      );
      _refresh();
    } catch (error) {
      if (mounted) showErrorSnackBar(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Headhunt Invites'),
        body: FutureBuilder<List<EmployerInvite>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return ApiErrorMessage(error: snapshot.error!, onRetry: _refresh);
            }

            final invites = snapshot.data ?? [];
            if (invites.isEmpty) {
              return const Center(child: Text('No headhunt invites yet.'));
            }

            return RefreshIndicator(
              onRefresh: () async {
                _refresh();
                await _future;
              },
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: invites.length,
                itemBuilder: (context, index) {
                  final invite = invites[index];
                  final unanswered = invite.response == 'no_response';
                  final responseLabel = unanswered
                      ? 'Awaiting your response'
                      : invite.response == 'applied'
                          ? 'Applied for job'
                          : 'Declined';

                  return Card(
                    child: ListTile(
                      title: Text(invite.jobTitle),
                      subtitle: Text('${invite.organizationName}\n$responseLabel'),
                      isThreeLine: true,
                      trailing: Wrap(
                        spacing: 4,
                        children: [
                          TextButton(
                            onPressed: () => context.push('/jobs/${invite.jobId}'),
                            child: const Text('View job'),
                          ),
                          if (unanswered)
                            TextButton(
                              onPressed: () => _decline(invite),
                              child: const Text('Decline'),
                            ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            );
          },
        ),
      ),
    );
  }
}
