import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getHRHeadAnalytics, getNotifications, getOrganization, getPendingHiringDecisions } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { getApiErrorMessage, titleize } from './hrHeadUtils.js';

function StatCard({ label, value, helper, tone = 'primary' }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack spacing={1}>
          <Typography color="text.secondary" variant="body2">
            {label}
          </Typography>
          <Typography component="p" variant="h4" sx={{ fontWeight: 700 }}>
            {value ?? 0}
          </Typography>
          {helper ? <Chip color={tone} label={helper} size="small" variant="outlined" sx={{ alignSelf: 'flex-start' }} /> : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

function ActionCard({ title, description, to, actionLabel, severity = 'info' }) {
  return (
    <Alert
      severity={severity}
      action={(
        <Button color="inherit" component={RouterLink} size="small" to={to}>
          {actionLabel}
        </Button>
      )}
    >
      <Typography sx={{ fontWeight: 700 }}>{title}</Typography>
      <Typography variant="body2">{description}</Typography>
    </Alert>
  );
}

function ProgressItem({ label, value, color = 'primary' }) {
  const normalizedValue = Number.isFinite(Number(value)) ? Math.min(Math.max(Number(value), 0), 100) : 0;
  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
        <Typography variant="body2">{label}</Typography>
        <Typography color="text.secondary" variant="body2">{normalizedValue}%</Typography>
      </Stack>
      <LinearProgress color={color} value={normalizedValue} variant="determinate" sx={{ height: 8, borderRadius: 999 }} />
    </Box>
  );
}

export default function HRHeadDashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [pendingDecisions, setPendingDecisions] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const loadDashboard = async () => {
      setIsLoading(true);
      setError('');
      try {
        const [analyticsResult, organizationResult, decisionsResult, notificationsResult] = await Promise.allSettled([
          getHRHeadAnalytics(),
          getOrganization(),
          getPendingHiringDecisions(),
          getNotifications(),
        ]);

        if (!isMounted) {
          return;
        }

        if (analyticsResult.status === 'fulfilled') {
          setDashboard(analyticsResult.value);
        }
        if (organizationResult.status === 'fulfilled') {
          setOrganization(organizationResult.value);
        }
        if (decisionsResult.status === 'fulfilled') {
          setPendingDecisions(decisionsResult.value);
        }
        if (notificationsResult.status === 'fulfilled') {
          setNotifications(notificationsResult.value);
        }
        if (analyticsResult.status === 'rejected' && organizationResult.status === 'rejected') {
          setError(getApiErrorMessage(analyticsResult.reason, 'Unable to load HR head dashboard.'));
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, 'Unable to load HR head dashboard.'));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadDashboard();

    return () => {
      isMounted = false;
    };
  }, []);

  const metrics = dashboard?.metrics ?? {};
  const unreadNotifications = useMemo(() => notifications.filter((notification) => !notification.is_read), [notifications]);
  const executiveActions = [
    {
      title: `${pendingDecisions.length} hiring approval${pendingDecisions.length === 1 ? '' : 's'} waiting`,
      description: 'Review recruiter recommendations, interview evidence, and final offer readiness before approval.',
      to: '/hr-head/hiring-decisions',
      actionLabel: 'Review approvals',
      severity: pendingDecisions.length ? 'warning' : 'success',
    },
    {
      title: organization ? `${organization.name} profile is ${organization.status}` : 'Organization profile incomplete',
      description: organization ? 'Keep company details, hiring contacts, and operational settings accurate for your team.' : 'Create the organization profile before inviting recruiters and interviewers.',
      to: '/hr-head/organization',
      actionLabel: 'Open profile',
      severity: organization ? 'info' : 'warning',
    },
    {
      title: `${unreadNotifications.length} unread notification${unreadNotifications.length === 1 ? '' : 's'}`,
      description: 'Track workflow events, approvals, and account updates that need HR department attention.',
      to: '/hr-head/notifications',
      actionLabel: 'View inbox',
      severity: unreadNotifications.length ? 'info' : 'success',
    },
  ];

  return (
    <Box>
      <HRHeadNav />
      <Stack spacing={3}>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
          <Box>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
              HR Department Head Dashboard
            </Typography>
            <Typography color="text.secondary">
              Executive overview of organization readiness, hiring approvals, pipeline health, and team governance.
            </Typography>
          </Box>
          <Button component={RouterLink} to="/hr-head/analytics" variant="contained">Open analytics</Button>
        </Stack>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading HR head dashboard" /> : null}

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Job postings" value={metrics.total_job_postings} helper="Org demand" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Applications" value={metrics.total_applications} helper="Talent volume" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Pending HR approvals" value={pendingDecisions.length} helper="Decision queue" tone={pendingDecisions.length ? 'warning' : 'success'} /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Unread notifications" value={unreadNotifications.length} helper="Inbox health" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Hiring success rate" value={`${metrics.hiring_success_rate ?? 0}%`} helper="Conversion" tone="success" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Rejection rate" value={`${metrics.rejection_rate ?? 0}%`} helper="Quality control" tone="warning" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Dropout rate" value={`${metrics.dropout_rate ?? 0}%`} helper="Candidate risk" tone="warning" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Offer acceptance rate" value={`${metrics.offer_acceptance_rate ?? 0}%`} helper="Closing strength" tone="success" /></Grid>
        </Grid>

        <Grid container spacing={2}>
          <Grid item xs={12} md={7}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography component="h3" variant="h6">Executive action center</Typography>
                <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>
                  Prioritized actions for approvals, organization administration, and unread workflow events.
                </Typography>
                <Stack spacing={2}>{executiveActions.map((action) => <ActionCard key={action.title} {...action} />)}</Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={5}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography component="h3" variant="h6">Pipeline health snapshot</Typography>
                <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>
                  Quick percentage indicators to spot conversion, dropout, and offer-closing risks.
                </Typography>
                <Stack spacing={2}>
                  <ProgressItem label="Hiring success" value={metrics.hiring_success_rate} color="success" />
                  <ProgressItem label="Offer acceptance" value={metrics.offer_acceptance_rate} color="success" />
                  <ProgressItem label="Rejection" value={metrics.rejection_rate} color="warning" />
                  <ProgressItem label="Candidate dropout" value={metrics.dropout_rate} color="error" />
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
                  <Box>
                    <Typography component="h3" variant="h6">Recent unread notifications</Typography>
                    <Typography color="text.secondary" variant="body2">Latest items that may require HR oversight.</Typography>
                  </Box>
                  <Button component={RouterLink} to="/hr-head/notifications" variant="outlined">Manage notifications</Button>
                </Stack>
                <Divider sx={{ my: 2 }} />
                <Stack spacing={1.5}>
                  {unreadNotifications.slice(0, 4).map((notification) => (
                    <Box key={notification.id}>
                      <Typography sx={{ fontWeight: 700 }}>{notification.title ?? titleize(notification.notification_type ?? 'Notification')}</Typography>
                      <Typography color="text.secondary" variant="body2">{notification.message ?? 'Open notification center for details.'}</Typography>
                    </Box>
                  ))}
                  {!unreadNotifications.length ? <Typography color="text.secondary">No unread notifications. Your HR queue is clear.</Typography> : null}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
