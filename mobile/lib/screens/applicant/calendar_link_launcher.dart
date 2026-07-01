import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher_string.dart';

import '../../models/applicant_interview.dart';

Future<void> openInterviewCalendarLink(
  BuildContext context,
  ApplicantInterview interview,
) {
  return _openCalendarLink(
    context,
    storedCalendarLink: interview.calendarLink,
  );
}

Future<void> _openCalendarLink(
  BuildContext context, {
  required String storedCalendarLink,
}) async {
  final link = _googleCalendarApiLink(storedCalendarLink);

  final launched = await launchUrlString(
    link,
    mode: LaunchMode.externalApplication,
  );
  if (!launched && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Unable to open the calendar link on this device.'),
      ),
    );
  }
}

String _googleCalendarApiLink(String storedCalendarLink) {
  final uri = Uri.tryParse(storedCalendarLink);
  final isGoogleCalendarLink =
      uri?.host == 'calendar.google.com' ||
      (uri?.host.endsWith('google.com') == true &&
          uri?.path.contains('calendar') == true);
  if (uri == null || !uri.hasScheme || !isGoogleCalendarLink) {
    throw StateError(
      'Interview calendar links must come from the Google Calendar API.',
    );
  }

  return storedCalendarLink;
}
