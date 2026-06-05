import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, CircularProgress, Grid, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getHRHeadAnalytics, getNotifications, getOrganization, getPendingHiringDecisions } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { getApiErrorMessage } from './hrHeadUtils.js';

function StatCard({ label, value }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography color="text.secondary" variant="body2">
          {label}
        </Typography>
        <Typography component="p" variant="h4" sx={{ fontWeight: 700 }}>
          {value ?? 0}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function HRHeadDashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
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
          setPendingCount(decisionsResult.value.length);
        }
        if (notificationsResult.status === 'fulfilled') {
          setUnreadCount(notificationsResult.value.filter((notification) => !notification.is_read).length);
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

  return (
    <Box>
      <HRHeadNav />
      <Stack spacing={3}>
        <Box>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
            HR Department Head Dashboard
          </Typography>
          <Typography color="text.secondary">
            Monitor organization setup, approvals, team activity, billing, and analytics from one place.
          </Typography>
        </Box>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading HR head dashboard" /> : null}

        <Alert severity={organization ? 'success' : 'info'}>
          {organization
            ? `Managing ${organization.name} (${organization.status}).`
            : 'Create your organization profile before managing team members, billing, and analytics.'}
        </Alert>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Job postings" value={metrics.total_job_postings} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Applications" value={metrics.total_applications} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Pending HR approvals" value={pendingCount} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Unread notifications" value={unreadCount} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Hiring success rate" value={`${metrics.hiring_success_rate ?? 0}%`} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Rejection rate" value={`${metrics.rejection_rate ?? 0}%`} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Dropout rate" value={`${metrics.dropout_rate ?? 0}%`} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Offer acceptance rate" value={`${metrics.offer_acceptance_rate ?? 0}%`} />
          </Grid>
        </Grid>

        <Card>
          <CardContent>
            <Typography component="h3" variant="h6" sx={{ mb: 2 }}>
              Quick actions
            </Typography>
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              <Button component={RouterLink} to="/hr-head/organization" variant="contained">
                Organization profile
              </Button>
              <Button component={RouterLink} to="/hr-head/team/create" variant="outlined">
                Create team member
              </Button>
              <Button component={RouterLink} to="/hr-head/hiring-decisions" variant="outlined">
                Review decisions
              </Button>
              <Button component={RouterLink} to="/hr-head/billing" variant="outlined">
                Manage billing
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
