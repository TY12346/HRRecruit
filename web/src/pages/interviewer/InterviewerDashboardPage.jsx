import { useEffect, useState } from 'react';
import { Alert, Box, Card, CardContent, CircularProgress, Grid, Paper, Typography } from '@mui/material';
import { getInterviewerAnalytics } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { getApiErrorMessage } from './interviewerUtils.js';

export default function InterviewerDashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getInterviewerAnalytics()
      .then((analyticsData) => setAnalytics(analyticsData))
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load interviewer dashboard.')))
      .finally(() => setIsLoading(false));
  }, []);

  const metrics = analytics?.metrics ?? {};

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>Interviewer Dashboard</Typography>

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
      </Paper>
    </Box>
  );
}
