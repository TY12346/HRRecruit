import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { getNotifications, markAllNotificationsRead, markNotificationRead } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './interviewerUtils.js';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]); const [error, setError] = useState(''); const [isLoading, setIsLoading] = useState(true);
  const load = () => getNotifications().then(setNotifications).catch((err) => setError(getApiErrorMessage(err, 'Unable to load notifications.'))).finally(() => setIsLoading(false));
  useEffect(() => { load(); }, []);
  const markOne = async (id) => { setError(''); try { await markNotificationRead(id); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to mark notification read.')); } };
  const markAll = async () => { setError(''); try { await markAllNotificationsRead(); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to mark all notifications read.')); } };
  return <Box><InterviewerNav /><Paper sx={{ p: 3 }}><Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 2 }}><Box><Typography variant="h5" sx={{ fontWeight: 700 }}>Notifications</Typography></Box><Button onClick={markAll} variant="outlined">Mark all read</Button></Stack>{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{isLoading ? <CircularProgress /> : null}<Stack spacing={2}>{notifications.map((notification) => <Card key={notification.id} variant="outlined"><CardContent><Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}><Box><Stack direction="row" spacing={1} alignItems="center"><Typography variant="h6">{notification.title}</Typography>{notification.is_read ? <Chip size="small" label="Read" /> : <Chip color="primary" size="small" label="Unread" />}</Stack><Typography>{notification.message}</Typography><Typography color="text.secondary">{titleize(notification.notification_type)} • {formatDateTime(notification.created_at)}</Typography></Box>{!notification.is_read ? <Button onClick={() => markOne(notification.id)} variant="contained">Mark read</Button> : null}</Stack></CardContent></Card>)}{!isLoading && notifications.length === 0 ? <Typography color="text.secondary">No notifications yet.</Typography> : null}</Stack></Paper></Box>;
}
