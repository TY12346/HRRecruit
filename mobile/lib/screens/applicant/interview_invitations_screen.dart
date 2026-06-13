import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/applicant_interview.dart';
import '../../services/applicant_workflow_service.dart';
import 'applicant_workflow_widgets.dart';
import '../../widgets/app_navigation.dart';

class InterviewInvitationsScreen extends StatefulWidget {
  const InterviewInvitationsScreen({super.key});

  @override
  State<InterviewInvitationsScreen> createState() => _InterviewInvitationsScreenState();
}

class _InterviewInvitationsScreenState extends State<InterviewInvitationsScreen> {
  late Future<List<InterviewInvitation>> _invitationsFuture;

  @override
  void initState() {
    super.initState();
    _invitationsFuture = _loadInvitations();
  }

  Future<List<InterviewInvitation>> _loadInvitations() {
    return context.read<ApplicantWorkflowService>().getInterviewInvitations();
  }

  void _refresh() {
    setState(() {
      _invitationsFuture = _loadInvitations();
    });
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'Interview invitations'),
        body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            _refresh();
            await _invitationsFuture;
          },
          child: FutureBuilder<List<InterviewInvitation>>(
            future: _invitationsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ApiErrorMessage(error: snapshot.error!, onRetry: _refresh);
              }
              final invitations = snapshot.data ?? [];
              if (invitations.isEmpty) {
                return const ApplicantWorkflowMessage(
                  icon: Icons.event_note_outlined,
                  title: 'No interview invitations yet',
                  message: 'When interviewers invite you, invitations will appear here.',
                );
              }
              return ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: invitations.length,
                itemBuilder: (context, index) {
                  final invitation = invitations[index];
                  return InterviewInvitationCard(
                    invitation: invitation,
                    onTap: () => context.push('/interview-invitations/${invitation.id}'),
                  );
                },
              );
            },
          ),
        ),
      ),
      ),
    );
  }
}
