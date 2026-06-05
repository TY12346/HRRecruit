import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, CircularProgress, Grid, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getApplications, getJobs, getNotifications, getRecruiterAnalytics } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';

function StatCard({ label, value }) {
  return <Card><CardContent><Typography color="text.secondary" variant="body2">{label}</Typography><Typography variant="h4" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography></CardContent></Card>;
}

export default function RecruiterDashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getRecruiterAnalytics(), getJobs(), getApplications(), getNotifications()])
      .then(([analyticsResult, jobsResult, applicationsResult, notificationsResult]) => {
        if (!active) return;
        if (analyticsResult.status === 'fulfilled') setAnalytics(analyticsResult.value);
        if (jobsResult.status === 'fulfilled') setJobs(jobsResult.value);
        if (applicationsResult.status === 'fulfilled') setApplications(applicationsResult.value);
        if (notificationsResult.status === 'fulfilled') setUnread(notificationsResult.value.filter((item) => !item.is_read).length);
        if (analyticsResult.status === 'rejected' && jobsResult.status === 'rejected') setError(getApiErrorMessage(analyticsResult.reason, 'Unable to load recruiter dashboard.'));
      })
      .finally(() => active && setIsLoading(false));
    return () => { active = false; };
  }, []);

  const metrics = analytics?.metrics ?? analytics ?? {};
  const pendingScreening = applications.filter((application) => ['submitted', 'screened'].includes(application.status)).length;

  return (
    <Box>
      <RecruiterNav />
      <Stack spacing={3}>
        <Box>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>Recruiter Dashboard</Typography>
          <Typography color="text.secondary">Manage jobs, AI screening, interviews, hiring decisions, offers, and notifications.</Typography>
        </Box>
        {error ? <Alert severity="error">{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading recruiter dashboard" /> : null}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Jobs" value={metrics.total_job_postings ?? jobs.length} /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Applications" value={metrics.total_applications ?? applications.length} /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Pending screening" value={pendingScreening} /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Unread notifications" value={unread} /></Grid>
        </Grid>
        <Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Quick actions</Typography><Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
          <Button component={RouterLink} to="/recruiter/jobs/create" variant="contained">Create job</Button>
          <Button component={RouterLink} to="/recruiter/applications" variant="outlined">Review applications</Button>
          <Button component={RouterLink} to="/recruiter/interviews" variant="outlined">Assign interviews</Button>
          <Button component={RouterLink} to="/recruiter/hiring-decisions" variant="outlined">Submit decisions</Button>
        </Stack></CardContent></Card>
      </Stack>
    </Box>
  );
}
