import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { getNotifications, markAllNotificationsRead, markNotificationRead } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './interviewerUtils.js';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [search, setSearch] = useState('');
  const [readFilter, setReadFilter] = useState('all');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const load = () => getNotifications()
    .then(setNotifications)
    .catch((err) => setError(getApiErrorMessage(err, 'Unable to load notifications.')))
    .finally(() => setIsLoading(false));

  useEffect(() => { load(); }, []);

  const filteredNotifications = useMemo(() => {
    const query = search.trim().toLowerCase();
    return notifications.filter((notification) => {
      const matchesRead = readFilter === 'all' || (readFilter === 'unread' ? !notification.is_read : notification.is_read);
      const matchesSearch = !query || [notification.title, notification.message, notification.notification_type]
        .some((value) => String(value ?? '').toLowerCase().includes(query));
      return matchesRead && matchesSearch;
    });
  }, [notifications, readFilter, search]);

  const markOne = async (id) => {
    setError('');
    try { await markNotificationRead(id); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to mark notification read.')); }
  };
  const markAll = async () => {
    setError('');
    try { await markAllNotificationsRead(); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to mark all notifications read.')); }
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 2 }}>Notifications</Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
          <TextField label="Search notifications" value={search} onChange={(event) => setSearch(event.target.value)} fullWidth />
          <TextField select label="Read status" value={readFilter} onChange={(event) => setReadFilter(event.target.value)} sx={{ minWidth: 180 }}>
            <MenuItem value="all">All notifications</MenuItem>
            <MenuItem value="unread">Unread</MenuItem>
            <MenuItem value="read">Read</MenuItem>
          </TextField>
          <Button onClick={markAll} variant="outlined">Mark all read</Button>
        </Stack>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        <Stack spacing={1}>
          {filteredNotifications.map((notification) => (
            <Stack key={notification.id} direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1} sx={{ py: 1 }}>
              <Box>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography sx={{ fontWeight: 700 }}>{notification.title}</Typography>
                  <Chip size="small" label={notification.is_read ? 'Read' : 'Unread'} color={notification.is_read ? 'default' : 'primary'} />
                </Stack>
                <Typography color="text.secondary" variant="body2">{titleize(notification.notification_type)} • {formatDateTime(notification.created_at)} • {notification.message}</Typography>
              </Box>
              {!notification.is_read ? <Button onClick={() => markOne(notification.id)} variant="contained" size="small">Mark read</Button> : null}
            </Stack>
          ))}
          {!isLoading && filteredNotifications.length === 0 ? <Typography color="text.secondary">No notifications found.</Typography> : null}
        </Stack>
      </Paper>
    </Box>
  );
}
