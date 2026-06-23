import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher_string.dart';

import '../../models/applicant_interview.dart';

const _googleCalendarRenderUrl = 'https://calendar.google.com/calendar/render';
const _localCalendarHost = 'calendar.hrrecruit.local';

Future<void> openInterviewCalendarLink(
  BuildContext context,
  ApplicantInterview interview,
) {
  final application = interview.application;
  return _openCalendarLink(
    context,
    storedCalendarLink: interview.calendarLink,
    title: application?.jobTitle.isNotEmpty == true
        ? 'Interview: ${application!.jobTitle}'
        : 'Interview',
    start: interview.scheduledDatetime,
    mode: interview.mode,
    meetingLink: interview.meetingLink,
    location: interview.location,
  );
}

Future<void> _openCalendarLink(
  BuildContext context, {
  required String storedCalendarLink,
  required String title,
  required DateTime? start,
  required String mode,
  required String meetingLink,
  required String location,
}) async {
  final link = _calendarLinkToLaunch(
    storedCalendarLink: storedCalendarLink,
    title: title,
    start: start,
    mode: mode,
    meetingLink: meetingLink,
    location: location,
  );

  final launched = await launchUrlString(
    link,
    mode: LaunchMode.externalApplication,
  );
  if (!launched && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Unable to open the calendar link on this device.')),
    );
  }
}

String _calendarLinkToLaunch({
  required String storedCalendarLink,
  required String title,
  required DateTime? start,
  required String mode,
  required String meetingLink,
  required String location,
}) {
  final uri = Uri.tryParse(storedCalendarLink);
  if (uri != null && uri.host != _localCalendarHost) {
    return storedCalendarLink;
  }
  return _buildGoogleCalendarTemplateLink(
    title: title,
    start: start,
    mode: mode,
    meetingLink: meetingLink,
    location: location,
  );
}

String _buildGoogleCalendarTemplateLink({
  required String title,
  required DateTime? start,
  required String mode,
  required String meetingLink,
  required String location,
}) {
  final queryParameters = <String, String>{
    'action': 'TEMPLATE',
    'text': title,
    'details': [
      'HRRecruit interview.',
      if (mode.isNotEmpty) 'Mode: $mode.',
      if (meetingLink.isNotEmpty) 'Meeting link: $meetingLink',
    ].join('\n'),
    if (meetingLink.isNotEmpty || location.isNotEmpty)
      'location': meetingLink.isNotEmpty ? meetingLink : location,
  };

  if (start != null) {
    final utcStart = start.toUtc();
    final utcEnd = utcStart.add(const Duration(hours: 1));
    queryParameters['dates'] =
        '${_formatGoogleDateTime(utcStart)}/${_formatGoogleDateTime(utcEnd)}';
  }

  return Uri.parse(_googleCalendarRenderUrl)
      .replace(queryParameters: queryParameters)
      .toString();
}

String _formatGoogleDateTime(DateTime value) {
  String twoDigits(int number) => number.toString().padLeft(2, '0');
  return '${value.year}'
      '${twoDigits(value.month)}'
      '${twoDigits(value.day)}T'
      '${twoDigits(value.hour)}'
      '${twoDigits(value.minute)}'
      '${twoDigits(value.second)}Z';
}
