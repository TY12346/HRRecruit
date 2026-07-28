import { useEffect, useState } from 'react';
import { Box, Button, Chip, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink, useParams } from 'react-router-dom';
import Alert from '../../components/TimedAlert.jsx';
import { getNotification, markNotificationRead } from '../../api/client.js';
import { useNotifications } from '../../notifications/NotificationContext.jsx';

export default function NotificationDetailPage({ Nav, basePath, formatDateTime }) {
  const { notificationId } = useParams();
  const { refreshNotifications } = useNotifications();
  const [notification, setNotification] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const current = await getNotification(notificationId);
        const viewed = current.is_read ? current : await markNotificationRead(notificationId);
        if (active) setNotification(viewed);
        await refreshNotifications();
      } catch {
        if (active) setError('Unable to load this notification.');
      } finally {
        if (active) setIsLoading(false);
      }
    };
    load();
    return () => { active = false; };
  }, [notificationId, refreshNotifications]);

  return (
    <Box>
      <Nav />
      <Paper sx={{ p: 3 }}>
        <Button component={RouterLink} to={basePath} sx={{ mb: 2 }}>← Back to notifications</Button>
        {error ? <Alert severity="error">{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading notification" /> : null}
        {notification ? (
          <Stack spacing={2}>
            <Typography component="h1" variant="h5" sx={{ fontWeight: 700 }}>{notification.title}</Typography>
            <Stack alignItems="center" direction="row" spacing={1}>
              <Chip label="Read" size="small" />
              <Typography color="text.secondary" variant="body2">{formatDateTime(notification.created_at)}</Typography>
            </Stack>
            <Typography sx={{ whiteSpace: 'pre-wrap' }}>{notification.message}</Typography>
            {notification.actions?.length ? (
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                {notification.actions.map((action) => (
                  <Button component={RouterLink} key={`${action.label}-${action.url}`} to={action.url} variant="contained">
                    {action.label}
                  </Button>
                ))}
              </Stack>
            ) : null}
          </Stack>
        ) : null}
      </Paper>
    </Box>
  );
}
