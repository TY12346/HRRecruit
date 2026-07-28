import { useEffect, useState } from 'react';
import { Box, Button, Chip, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import Alert from '../../components/TimedAlert.jsx';
import { markAllNotificationsRead } from '../../api/client.js';
import { useNotifications } from '../../notifications/NotificationContext.jsx';

export default function NotificationListPage({ Nav, basePath, formatDateTime }) {
  const { notifications, refreshNotifications } = useNotifications();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    refreshNotifications().catch(() => setError('Unable to load notifications.')).finally(() => setIsLoading(false));
  }, [refreshNotifications]);

  const markAll = async () => {
    setError('');
    try {
      await markAllNotificationsRead();
      await refreshNotifications();
    } catch {
      setError('Unable to mark all notifications as read.');
    }
  };

  return (
    <Box>
      <Nav />
      <Paper sx={{ p: 3 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 2 }}>
          <Typography component="h1" variant="h5" sx={{ fontWeight: 700 }}>Notifications</Typography>
          <Button disabled={!notifications.some((item) => !item.is_read)} onClick={markAll} variant="outlined">Mark all as read</Button>
        </Stack>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading notifications" /> : null}
        <Stack spacing={0}>
          {notifications.map((notification) => (
            <Stack
              alignItems={{ sm: 'center' }}
              direction={{ xs: 'column', sm: 'row' }}
              justifyContent="space-between"
              key={notification.id}
              spacing={2}
              sx={{ borderTop: '1px solid', borderColor: 'divider', py: 2, '&:first-of-type': { borderTop: 0 } }}
            >
              <Stack spacing={0.75}>
                <Typography component="h2" sx={{ fontWeight: 700 }}>{notification.title}</Typography>
                <Stack alignItems="center" direction="row" spacing={1}>
                  <Chip color={notification.is_read ? 'default' : 'primary'} label={notification.is_read ? 'Read' : 'Unread'} size="small" />
                  <Typography color="text.secondary" variant="body2">{formatDateTime(notification.created_at)}</Typography>
                </Stack>
              </Stack>
              <Button component={RouterLink} size="small" to={`${basePath}/${notification.id}`} variant="contained">View</Button>
            </Stack>
          ))}
          {!isLoading && notifications.length === 0 ? <Typography color="text.secondary">No notifications yet.</Typography> : null}
        </Stack>
      </Paper>
    </Box>
  );
}
