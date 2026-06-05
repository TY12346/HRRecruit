import { useEffect, useState } from 'react';
import { Alert, Box, Card, CardContent, CircularProgress, Grid, Paper, Stack, Typography } from '@mui/material';
import { Bar } from 'react-chartjs-2';
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js';
import { getRecruiterAnalytics } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage, titleize } from './recruiterUtils.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

function Stat({ label, value }) { return <Card><CardContent><Typography color="text.secondary">{label}</Typography><Typography variant="h4" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography></CardContent></Card>; }

export default function RecruiterAnalyticsPage() {
  const [analytics, setAnalytics] = useState(null); const [error, setError] = useState(''); const [isLoading, setIsLoading] = useState(true);
  useEffect(() => { getRecruiterAnalytics().then(setAnalytics).catch((err) => setError(getApiErrorMessage(err, 'Unable to load analytics.'))).finally(() => setIsLoading(false)); }, []);
  const metrics = analytics?.metrics ?? analytics ?? {}; const statusBreakdown = metrics.application_status_breakdown ?? analytics?.application_status_breakdown ?? {};
  const chartData = { labels: Object.keys(statusBreakdown).map(titleize), datasets: [{ label: 'Applications', data: Object.values(statusBreakdown), backgroundColor: '#2563eb' }] };
  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}><Typography variant="h5" sx={{ fontWeight: 700 }}>Recruiter analytics</Typography><Typography color="text.secondary" sx={{ mb: 2 }}>Track recruitment pipeline performance for the FYP demo.</Typography>{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{isLoading ? <CircularProgress /> : <Stack spacing={3}><Grid container spacing={2}>{Object.entries(metrics).filter(([, value]) => typeof value !== 'object').slice(0, 8).map(([key, value]) => <Grid item xs={12} sm={6} md={3} key={key}><Stat label={titleize(key)} value={value} /></Grid>)}</Grid><Card><CardContent><Typography variant="h6">Application status breakdown</Typography>{Object.keys(statusBreakdown).length ? <Bar data={chartData} /> : <Typography color="text.secondary">No status data yet.</Typography>}</CardContent></Card></Stack>}</Paper></Box>;
}
