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
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getAssignedInterviews, getInterviewerAnalytics, getNotifications } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import ApplicantJobSummary from '../../components/ApplicantJobSummary.jsx';
import { candidateName, formatDateTime, getApiErrorMessage, jobTitle, titleize } from './interviewerUtils.js';

function MetricCard({ label, value, helper, tone = 'primary' }) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Stack spacing={1}>
          <Typography color="text.secondary" variant="body2">{label}</Typography>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography>
          {helper ? <Chip color={tone} label={helper} size="small" variant="outlined" sx={{ alignSelf: 'flex-start' }} /> : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

function InterviewRow({ interview }) {
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
      <Box>
        <ApplicantJobSummary applicantName={candidateName(interview)} jobTitle={jobTitle(interview)} />
        <Typography color="text.secondary" variant="body2">
          {formatDateTime(interview.scheduled_datetime)} • {titleize(interview.mode)} • {interview.meeting_link || interview.location || 'No venue yet'}
        </Typography>
      </Box>
      <Stack direction="row" spacing={1} alignItems="center">
        <Chip label={titleize(interview.status)} size="small" />
        <Button component={RouterLink} to={`/interviewer/interviews/${interview.id}`} size="small" variant="outlined">Open</Button>
      </Stack>
    </Stack>
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

export default function InterviewerDashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [interviews, setInterviews] = useState([]);
  const [unreadNotifications, setUnreadNotifications] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    Promise.allSettled([getInterviewerAnalytics(), getAssignedInterviews(), getNotifications()])
      .then(([analyticsResult, interviewsResult, notificationsResult]) => {
        if (!isMounted) return;
        if (analyticsResult.status === 'fulfilled') setAnalytics(analyticsResult.value);
        if (interviewsResult.status === 'fulfilled') setInterviews(interviewsResult.value);
        if (notificationsResult.status === 'fulfilled') setUnreadNotifications(notificationsResult.value.filter((item) => !item.is_read));
        if (analyticsResult.status === 'rejected' && interviewsResult.status === 'rejected') {
          setError(getApiErrorMessage(analyticsResult.reason, 'Unable to load interviewer dashboard.'));
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const metrics = analytics?.metrics ?? {};
  const upcomingInterviews = useMemo(() => interviews
    .filter((interview) => ['assigned', 'scheduled'].includes(interview.status))
    .sort((a, b) => new Date(a.scheduled_datetime ?? 0) - new Date(b.scheduled_datetime ?? 0))
    .slice(0, 5), [interviews]);
  const pendingEvaluations = interviews.filter((interview) => interview.status === 'completed' && !interview.evaluation_submitted).length;
  const completionRate = metrics.assigned_interviews ? Math.round(((metrics.completed_interviews ?? 0) / metrics.assigned_interviews) * 100) : 0;

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Stack spacing={3}>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
            <Box>
              <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>Interviewer Dashboard</Typography>
              <Typography color="text.secondary">Focus on upcoming interviews, evaluation quality, transcript follow-up, and candidate evidence.</Typography>
            </Box>
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              <Button component={RouterLink} to="/interviewer/interviews" variant="contained">View interviews</Button>
              <Button component={RouterLink} to="/interviewer/availability" variant="outlined">Manage availability</Button>
            </Stack>
          </Stack>

          {error ? <Alert severity="error">{error}</Alert> : null}
          {isLoading ? <CircularProgress aria-label="Loading interviewer dashboard" /> : null}

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}><MetricCard label="Assigned interviews" value={metrics.assigned_interviews ?? interviews.length} helper="Total workload" /></Grid>
            <Grid item xs={12} sm={6} md={3}><MetricCard label="Completed interviews" value={metrics.completed_interviews} helper={`${completionRate}% completion`} tone="success" /></Grid>
            <Grid item xs={12} sm={6} md={3}><MetricCard label="Evaluations submitted" value={metrics.interviewer_evaluation_count} helper="Evidence captured" tone="success" /></Grid>
            <Grid item xs={12} sm={6} md={3}><MetricCard label="Average score" value={metrics.average_evaluation_score} helper="Panel signal" /></Grid>
            <Grid item xs={12} sm={6} md={3}><MetricCard label="Upcoming interviews" value={upcomingInterviews.length} helper="Scheduled queue" /></Grid>
            <Grid item xs={12} sm={6} md={3}><MetricCard label="Pending evaluations" value={pendingEvaluations} helper="Needs submission" tone={pendingEvaluations ? 'warning' : 'success'} /></Grid>
            <Grid item xs={12} sm={6} md={3}><MetricCard label="Unread notifications" value={unreadNotifications.length} helper="Inbox" /></Grid>
            <Grid item xs={12} sm={6} md={3}><MetricCard label="Offer acceptance" value={`${metrics.offer_acceptance_rate ?? 0}%`} helper="Candidate outcomes" tone="success" /></Grid>
          </Grid>

          <Grid container spacing={2}>
            <Grid item xs={12} md={7}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
                    <Box>
                      <Typography component="h3" variant="h6">Upcoming interview agenda</Typography>
                      <Typography color="text.secondary" variant="body2">Prepare candidate context, interview mode, and meeting location before each session.</Typography>
                    </Box>
                    <Button component={RouterLink} to="/interviewer/interviews" variant="outlined">Open calendar</Button>
                  </Stack>
                  <Divider sx={{ my: 2 }} />
                  <Stack spacing={1.5} divider={<Divider flexItem />}>
                    {upcomingInterviews.map((interview) => <InterviewRow key={interview.id} interview={interview} />)}
                    {!upcomingInterviews.length ? <Typography color="text.secondary">No upcoming interviews assigned.</Typography> : null}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={5}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography component="h3" variant="h6">Performance and follow-up</Typography>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>Use these signals to keep interview feedback timely and useful for recruiters.</Typography>
                  <Stack spacing={2}>
                    <ProgressItem label="Interview completion" value={completionRate} color="success" />
                    <ProgressItem label="Offer acceptance for assigned candidates" value={metrics.offer_acceptance_rate} color="success" />
                    <ProgressItem label="Candidate dropout" value={metrics.dropout_rate} color="warning" />
                    <Alert severity={pendingEvaluations ? 'warning' : 'success'}>
                      {pendingEvaluations ? `${pendingEvaluations} completed interview${pendingEvaluations === 1 ? '' : 's'} still need evaluation submission.` : 'All completed interviews have evaluation coverage.'}
                    </Alert>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography component="h3" variant="h6">Interviewer quick actions</Typography>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>Access candidate evidence, transcripts, evaluation forms, and notification updates.</Typography>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    <Button component={RouterLink} to="/interviewer/candidates" variant="outlined">Assigned candidates</Button>
                    <Button component={RouterLink} to="/interviewer/interviews" variant="outlined">View interviews</Button>
                    <Button component={RouterLink} to="/interviewer/analytics" variant="outlined">Review analytics</Button>
                    <Button component={RouterLink} to="/interviewer/notifications" variant="outlined">Check notifications</Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Stack>
      </Paper>
    </Box>
  );
}
