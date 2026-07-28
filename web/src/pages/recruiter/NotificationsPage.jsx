import NotificationListPage from '../notifications/NotificationListPage.jsx';
import NotificationDetailPage from '../notifications/NotificationDetailPage.jsx';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime } from './recruiterUtils.js';

const props = { Nav: RecruiterNav, basePath: '/recruiter/notifications', formatDateTime };

export default function RecruiterNotificationsPage() {
  return <NotificationListPage {...props} />;
}

export function RecruiterNotificationDetailPage() {
  return <NotificationDetailPage {...props} />;
}
