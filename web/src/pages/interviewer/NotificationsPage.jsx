import NotificationListPage from '../notifications/NotificationListPage.jsx';
import NotificationDetailPage from '../notifications/NotificationDetailPage.jsx';
import InterviewerNav from './InterviewerNav.jsx';
import { formatDateTime } from './interviewerUtils.js';

const props = { Nav: InterviewerNav, basePath: '/interviewer/notifications', formatDateTime };

export default function InterviewerNotificationsPage() {
  return <NotificationListPage {...props} />;
}

export function InterviewerNotificationDetailPage() {
  return <NotificationDetailPage {...props} />;
}
