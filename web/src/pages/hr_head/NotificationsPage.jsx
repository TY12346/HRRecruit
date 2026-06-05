import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Stack,
  Typography,
} from '@mui/material';
import { getNotifications, markAllNotificationsRead, markNotificationRead } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './hrHeadUtils.js';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [markingId, setMarkingId] = useState(null);

  const loadNotifications = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getNotifications();
      setNotifications(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, 'Unable to load notifications.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadInitialNotifications = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getNotifications();
        if (isMounted) {
          setNotifications(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, 'Unable to load notifications.'));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadInitialNotifications();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleMarkRead = async (notification) => {
    setMarkingId(notification.id);
    setError('');
    setSuccessMessage('');
    try {
      await markNotificationRead(notification.id);
      await loadNotifications();
    } catch (markError) {
      setError(getApiErrorMessage(markError, 'Unable to mark notification as read.'));
    } finally {
      setMarkingId(null);
    }
  };

  const handleMarkAllRead = async () => {
    setError('');
    setSuccessMessage('');
    try {
      const response = await markAllNotificationsRead();
      setSuccessMessage(`${response.updated_count ?? 0} notifications marked as read.`);
      await loadNotifications();
    } catch (markError) {
      setError(getApiErrorMessage(markError, 'Unable to mark all notifications as read.'));
    }
  };

  return (
    <Box>
      <HRHeadNav />
      <Stack spacing={3}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={2}>
          <Box>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
              Notifications
            </Typography>
            <Typography color="text.secondary">
              View HR approval, billing, and organization alerts.
            </Typography>
          </Box>
          <Button onClick={handleMarkAllRead} variant="outlined">Mark all as read</Button>
        </Stack>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading notifications" /> : null}
        {!isLoading && notifications.length === 0 ? <Alert severity="info">No notifications yet.</Alert> : null}

        {notifications.map((notification) => (
          <Card key={notification.id} sx={{ borderLeft: notification.is_read ? '4px solid transparent' : '4px solid #2563eb' }}>
            <CardContent>
              <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={2}>
                <Box>
                  <Stack alignItems="center" direction="row" spacing={1} sx={{ mb: 1 }}>
                    <Typography component="h3" variant="h6">{notification.title}</Typography>
                    <Chip color={notification.is_read ? 'default' : 'primary'} label={notification.is_read ? 'Read' : 'Unread'} size="small" />
                  </Stack>
                  <Typography sx={{ mb: 1 }}>{notification.message}</Typography>
                  <Typography color="text.secondary" variant="body2">
                    {titleize(notification.notification_type)} • {formatDateTime(notification.created_at)}
                  </Typography>
                </Box>
                <Button
                  disabled={notification.is_read || markingId === notification.id}
                  onClick={() => handleMarkRead(notification)}
                  variant="outlined"
                >
                  {markingId === notification.id ? 'Marking…' : 'Mark read'}
                </Button>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Box>
  );
}
