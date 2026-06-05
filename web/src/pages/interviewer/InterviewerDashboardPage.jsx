import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, CircularProgress, Grid, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getAssignedInterviews, getInterviewerAnalytics } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { candidateName, formatDateTime, getApiErrorMessage, jobTitle, latestInviteStatus, titleize } from './interviewerUtils.js';

export default function InterviewerDashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [interviews, setInterviews] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([getInterviewerAnalytics(), getAssignedInterviews()])
      .then(([analyticsData, interviewData]) => {
        setAnalytics(analyticsData);
        setInterviews(interviewData);
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load interviewer dashboard.')))
      .finally(() => setIsLoading(false));
  }, []);

  const metrics = analytics?.metrics ?? {};
  const upcoming = interviews.filter((interview) => ['assigned', 'invitation_sent', 'scheduled'].includes(interview.status)).slice(0, 5);

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>Interviewer Dashboard</Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>Review assigned candidates, manage interview invitations, upload recordings, and submit evaluations.</Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            ['Assigned interviews', metrics.assigned_interviews],
            ['Completed interviews', metrics.completed_interviews],
            ['Evaluations submitted', metrics.interviewer_evaluation_count],
            ['Average score', metrics.average_evaluation_score],
          ].map(([label, value]) => (
            <Grid item xs={12} sm={6} md={3} key={label}>
              <Card variant="outlined"><CardContent><Typography color="text.secondary">{label}</Typography><Typography variant="h4" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography></CardContent></Card>
            </Grid>
          ))}
        </Grid>
        <Stack direction="row" spacing={1} sx={{ mb: 2 }} useFlexGap flexWrap="wrap">
          <Button component={RouterLink} to="/interviewer/candidates" variant="contained">View assigned candidates</Button>
          <Button component={RouterLink} to="/interviewer/interviews" variant="outlined">Manage interviews</Button>
        </Stack>
        <Typography variant="h6" sx={{ mb: 1 }}>Upcoming work</Typography>
        <Stack spacing={2}>
          {upcoming.map((interview) => (
            <Card key={interview.id} variant="outlined">
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{candidateName(interview)} • {jobTitle(interview)}</Typography>
                    <Typography color="text.secondary">{titleize(interview.status)} • Invite: {latestInviteStatus(interview)} • {formatDateTime(interview.scheduled_datetime ?? interview.latest_invitation?.proposed_datetime)}</Typography>
                  </Box>
                  <Button component={RouterLink} to={`/interviewer/interviews/${interview.id}`} variant="outlined">Open</Button>
                </Stack>
              </CardContent>
            </Card>
          ))}
          {!isLoading && upcoming.length === 0 ? <Typography color="text.secondary">No upcoming interviews assigned yet.</Typography> : null}
        </Stack>
      </Paper>
    </Box>
  );
}
