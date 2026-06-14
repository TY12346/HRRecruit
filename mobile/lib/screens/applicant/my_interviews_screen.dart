import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/applicant_interview.dart';
import '../../services/applicant_workflow_service.dart';
import 'applicant_workflow_widgets.dart';
import '../../widgets/app_navigation.dart';

class MyInterviewsScreen extends StatefulWidget {
  const MyInterviewsScreen({super.key});

  @override
  State<MyInterviewsScreen> createState() => _MyInterviewsScreenState();
}

class _MyInterviewsScreenState extends State<MyInterviewsScreen> {
  late Future<List<ApplicantInterview>> _interviewsFuture;

  @override
  void initState() {
    super.initState();
    _interviewsFuture = _loadInterviews();
  }

  Future<List<ApplicantInterview>> _loadInterviews() {
    return context.read<ApplicantWorkflowService>().getInterviews();
  }

  void _refresh() {
    setState(() {
      _interviewsFuture = _loadInterviews();
    });
  }

  @override
  Widget build(BuildContext context) {
    return AppBackScope(
      child: Scaffold(
        appBar: appScreenAppBar(context, title: 'My interviews'),
        body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            _refresh();
            await _interviewsFuture;
          },
          child: FutureBuilder<List<ApplicantInterview>>(
            future: _interviewsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ApiErrorMessage(error: snapshot.error!, onRetry: _refresh);
              }
              final interviews = snapshot.data ?? [];
              if (interviews.isEmpty) {
                return const ApplicantWorkflowMessage(
                  icon: Icons.event_outlined,
                  title: 'No interviews yet',
                  message: 'Accepted, upcoming, and completed interviews will appear here.',
                );
              }

              final upcoming = interviews.where((interview) => !interview.isCompleted).toList();
              final completed = interviews.where((interview) => interview.isCompleted).toList();
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (upcoming.isNotEmpty) ...[
                    Text('Upcoming', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    ...upcoming.map((interview) => InterviewCard(interview: interview)),
                  ],
                  if (completed.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text('Completed', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    ...completed.map((interview) => InterviewCard(interview: interview)),
                  ],
                ],
              );
            },
          ),
        ),
      ),
      ),
    );
  }
}
