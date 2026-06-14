import { useEffect, useState } from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import { ArcElement, BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { downloadAnalyticsReportPdf, getInterviewerAnalytics } from '../../api/client.js';
import {
  barChartOptions,
  chartHeight,
  compactChartOptions,
  downloadBlob,
  percentageDoughnut,
  singleValueBar,
} from '../analytics/analyticsChartUtils.js';
import InterviewerNav from './InterviewerNav.jsx';
import { getApiErrorMessage, titleize } from './interviewerUtils.js';

ChartJS.register(ArcElement, BarElement, CategoryScale, Legend, LinearScale, Tooltip);

function MetricCard({ label, value }) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Typography color="text.secondary" variant="body2">{label}</Typography>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography>
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, description, children }) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6">{title}</Typography>
        {description ? <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>{description}</Typography> : null}
        <Box sx={chartHeight}>{children}</Box>
      </CardContent>
    </Card>
  );
}

export default function InterviewerAnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    getInterviewerAnalytics()
      .then((data) => {
        if (isMounted) setAnalytics(data);
      })
      .catch((err) => {
        if (isMounted) setError(getApiErrorMessage(err, 'Unable to load analytics.'));
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleExportPdf = async () => {
    setIsExporting(true);
    setError('');
    try {
      const pdfBlob = await downloadAnalyticsReportPdf('interviewer');
      downloadBlob(pdfBlob, 'interviewer-summary.pdf');
    } catch (exportError) {
      setError(getApiErrorMessage(exportError, 'Unable to export interviewer analytics PDF.'));
    } finally {
      setIsExporting(false);
    }
  };

  const metrics = analytics?.metrics ?? {};
  const charts = analytics?.charts ?? {};
  const timeToHireChart = singleValueBar('Average time-to-hire', metrics.average_time_to_hire_days, 'Days', '#7c3aed');
  const offerAcceptanceChart = percentageDoughnut('Accepted offers', metrics.offer_acceptance_rate, '#16a34a');
  const performanceChart = {
    labels: ['Assigned', 'Completed', 'Evaluations', 'Average score'],
    datasets: [
      {
        label: 'Interviewer performance',
        data: [
          metrics.assigned_interviews ?? 0,
          metrics.completed_interviews ?? 0,
          metrics.interviewer_evaluation_count ?? 0,
          metrics.average_evaluation_score ?? 0,
        ],
        backgroundColor: ['#2563eb', '#16a34a', '#f97316', '#7c3aed'],
      },
    ],
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" gap={2} sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Interviewer Analytics</Typography>

          </Box>
          <Button variant="outlined" onClick={handleExportPdf} disabled={isExporting || isLoading}>
            {isExporting ? 'Exporting…' : 'Export PDF'}
          </Button>
        </Stack>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : (
          <Stack spacing={3}>
            <Grid container spacing={2}>
              {Object.entries({
                assigned_interviews: metrics.assigned_interviews,
                completed_interviews: metrics.completed_interviews,
                interviewer_evaluation_count: metrics.interviewer_evaluation_count,
                average_evaluation_score: metrics.average_evaluation_score,
                dropout_rate: `${metrics.dropout_rate ?? 0}%`,
                offer_acceptance_rate: `${metrics.offer_acceptance_rate ?? 0}%`,
              }).map(([label, value]) => (
                <Grid item xs={12} sm={6} md={2} key={label}>
                  <MetricCard label={titleize(label)} value={value} />
                </Grid>
              ))}
            </Grid>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <ChartCard title="Applications by status" description="Statuses for candidates assigned to your interviews.">
                  {charts.applications_by_status ? <Doughnut data={charts.applications_by_status} options={compactChartOptions} /> : <Typography color="text.secondary">No chart data.</Typography>}
                </ChartCard>
              </Grid>
              <Grid item xs={12} md={6}>
                <ChartCard title="Candidate funnel" description="Assigned candidates grouped by recruitment stage.">
                  {charts.candidate_funnel ? <Bar data={charts.candidate_funnel} options={barChartOptions} /> : <Typography color="text.secondary">No chart data.</Typography>}
                </ChartCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <ChartCard title="Time-to-hire" description="Average days for assigned candidates that reached hired status.">
                  <Bar data={timeToHireChart} options={barChartOptions} />
                </ChartCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <ChartCard title="Offer acceptance rate" description="Accepted offers for your assigned candidates.">
                  <Doughnut data={offerAcceptanceChart} options={compactChartOptions} />
                </ChartCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <ChartCard title="Interviewer performance" description="Assignments, completions, submitted evaluations, and average score.">
                  <Bar data={performanceChart} options={barChartOptions} />
                </ChartCard>
              </Grid>
            </Grid>

            <Typography color="text.secondary">Organization: {analytics?.organization?.name ?? '—'}</Typography>
          </Stack>
        )}
      </Paper>
    </Box>
  );
}
