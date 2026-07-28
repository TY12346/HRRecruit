import NotificationListPage from '../notifications/NotificationListPage.jsx';
import NotificationDetailPage from '../notifications/NotificationDetailPage.jsx';
import HiringManagerNav from './HiringManagerNav.jsx';
import { formatDateTime } from './hiringManagerUtils.js';

const props = { Nav: HiringManagerNav, basePath: '/hiring-manager/notifications', formatDateTime };

export default function HiringManagerNotificationsPage() {
  return <NotificationListPage {...props} />;
}

export function HiringManagerNotificationDetailPage() {
  return <NotificationDetailPage {...props} />;
}
