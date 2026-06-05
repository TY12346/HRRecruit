import { useEffect, useState } from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import { ArcElement, BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js';
import { Alert, Box, Card, CardContent, CircularProgress, Grid, Paper, Stack, Typography } from '@mui/material';
import { getInterviewerAnalytics } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { getApiErrorMessage, titleize } from './interviewerUtils.js';

ChartJS.register(ArcElement, BarElement, CategoryScale, Legend, LinearScale, Tooltip);

export default function InterviewerAnalyticsPage() {
  const [analytics, setAnalytics] = useState(null); const [error, setError] = useState(''); const [isLoading, setIsLoading] = useState(true);
  useEffect(() => { getInterviewerAnalytics().then(setAnalytics).catch((err) => setError(getApiErrorMessage(err, 'Unable to load analytics.'))).finally(() => setIsLoading(false)); }, []);
  const metrics = analytics?.metrics ?? {}; const charts = analytics?.charts ?? {};
  return <Box><InterviewerNav /><Paper sx={{ p: 3 }}><Typography variant="h5" sx={{ fontWeight: 700 }}>Interviewer Analytics</Typography><Typography color="text.secondary" sx={{ mb: 2 }}>Performance and candidate pipeline metrics for your assigned interviews.</Typography>{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{isLoading ? <CircularProgress /> : null}<Grid container spacing={2} sx={{ mb: 3 }}>{Object.entries({ assigned_interviews: metrics.assigned_interviews, completed_interviews: metrics.completed_interviews, interviewer_evaluation_count: metrics.interviewer_evaluation_count, average_evaluation_score: metrics.average_evaluation_score, dropout_rate: metrics.dropout_rate }).map(([label, value]) => <Grid item xs={12} sm={6} md={2.4} key={label}><Card variant="outlined"><CardContent><Typography color="text.secondary">{titleize(label)}</Typography><Typography variant="h5" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography></CardContent></Card></Grid>)}</Grid><Grid container spacing={2}><Grid item xs={12} md={6}><Card variant="outlined"><CardContent><Typography variant="h6">Applications by status</Typography>{charts.applications_by_status ? <Doughnut data={charts.applications_by_status} /> : <Typography color="text.secondary">No chart data.</Typography>}</CardContent></Card></Grid><Grid item xs={12} md={6}><Card variant="outlined"><CardContent><Typography variant="h6">Candidate funnel</Typography>{charts.candidate_funnel ? <Bar data={charts.candidate_funnel} /> : <Typography color="text.secondary">No chart data.</Typography>}</CardContent></Card></Grid></Grid><Stack sx={{ mt: 2 }}><Typography color="text.secondary">Organization: {analytics?.organization?.name ?? '—'}</Typography></Stack></Paper></Box>;
}
