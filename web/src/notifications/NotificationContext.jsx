import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Alert, Button, Snackbar } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { getNotifications } from '../api/client.js';
import { useAuthStore } from '../store/authStore.js';

const NotificationContext = createContext({ notifications: [], unreadCount: 0, refreshNotifications: () => {} });
const POLL_INTERVAL_MS = 15000;

function notificationPath(role, notificationId) {
  const portal = role === 'hr_head' ? 'hiring-manager' : role;
  return `/${portal}/notifications/${notificationId}`;
}

export function NotificationProvider({ children }) {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const [notifications, setNotifications] = useState([]);
  const [popup, setPopup] = useState(null);
  const knownIds = useRef(new Set());
  const initialized = useRef(false);

  const refreshNotifications = useCallback(async ({ showPopup = false } = {}) => {
    if (!isAuthenticated || !['recruiter', 'interviewer', 'hr_head'].includes(user?.role)) return [];
    const data = await getNotifications();
    const unread = data.filter((item) => !item.is_read);
    if (showPopup && document.visibilityState === 'visible') {
      const newest = unread.find((item) => !knownIds.current.has(item.id));
      if (newest) setPopup(newest);
    }
    knownIds.current = new Set(data.map((item) => item.id));
    initialized.current = true;
    setNotifications(data);
    return data;
  }, [isAuthenticated, user?.role]);

  useEffect(() => {
    if (!isAuthenticated) {
      setNotifications([]);
      setPopup(null);
      knownIds.current = new Set();
      initialized.current = false;
      return undefined;
    }
    refreshNotifications({ showPopup: false }).catch(() => {});
    const interval = window.setInterval(() => {
      refreshNotifications({ showPopup: initialized.current }).catch(() => {});
    }, POLL_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [isAuthenticated, refreshNotifications]);

  const unreadCount = notifications.filter((item) => !item.is_read).length;
  const viewPopup = () => {
    const notification = popup;
    setPopup(null);
    if (notification) navigate(notificationPath(user?.role, notification.id));
  };

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, refreshNotifications }}>
      {children}
      <Snackbar anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }} open={Boolean(popup)} onClose={() => setPopup(null)}>
        <Alert
          action={<Button color="inherit" onClick={viewPopup} size="small">View</Button>}
          onClose={() => setPopup(null)}
          severity="info"
          variant="filled"
          sx={{ width: '100%' }}
        >
          {popup?.title}
        </Alert>
      </Snackbar>
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  return useContext(NotificationContext);
}
