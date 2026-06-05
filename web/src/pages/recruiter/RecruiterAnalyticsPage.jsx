import { useEffect, useState } from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
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
import { downloadAnalyticsReportPdf, getRecruiterAnalytics } from '../../api/client.js';
import {
  barChartOptions,
  chartFromMap,
  chartHeight,
  compactChartOptions,
  downloadBlob,
  percentageDoughnut,
  singleValueBar,
} from '../analytics/analyticsChartUtils.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage, titleize } from './recruiterUtils.js';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function Stat({ label, value }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography color="text.secondary" variant="body2">{label}</Typography>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography>
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, description, children }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography component="h3" variant="h6">{title}</Typography>
        {description ? <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>{description}</Typography> : null}
        <Box sx={chartHeight}>{children}</Box>
      </CardContent>
    </Card>
  );
}

export default function RecruiterAnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    getRecruiterAnalytics()
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
      const pdfBlob = await downloadAnalyticsReportPdf('recruiter');
      downloadBlob(pdfBlob, 'recruiter-summary.pdf');
    } catch (exportError) {
      setError(getApiErrorMessage(exportError, 'Unable to export recruiter analytics PDF.'));
    } finally {
      setIsExporting(false);
    }
  };

  const metrics = analytics?.metrics ?? analytics ?? {};
  const charts = analytics?.charts ?? {};
  const statusBreakdown = metrics.applications_by_status ?? analytics?.application_status_breakdown ?? {};
  const applicationsByStatusChart = charts.applications_by_status ?? chartFromMap(statusBreakdown, 'Applications', titleize);
  const candidateFunnelChart = charts.candidate_funnel;
  const timeToHireChart = singleValueBar('Average time-to-hire', metrics.average_time_to_hire_days, 'Days', '#7c3aed');
  const offerAcceptanceChart = percentageDoughnut('Accepted offers', metrics.offer_acceptance_rate, '#16a34a');
  const performanceChart = {
    labels: ['Hires', 'Evaluations submitted'],
    datasets: [
      {
        label: 'Recruiter performance',
        data: [metrics.recruiter_hire_count ?? metrics.hired_count ?? 0, metrics.interviewer_evaluation_count ?? 0],
        backgroundColor: ['#16a34a', '#f97316'],
      },
    ],
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" gap={2} sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Recruiter analytics</Typography>
            <Typography color="text.secondary">Track applications, candidate funnel, hiring speed, offers, and recruiter performance.</Typography>
          </Box>
          <Button variant="outlined" onClick={handleExportPdf} disabled={isExporting || isLoading}>
            {isExporting ? 'Exporting…' : 'Export PDF'}
          </Button>
        </Stack>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : (
          <Stack spacing={3}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}><Stat label="Job postings" value={metrics.total_job_postings} /></Grid>
              <Grid item xs={12} sm={6} md={3}><Stat label="Applications" value={metrics.total_applications} /></Grid>
              <Grid item xs={12} sm={6} md={3}><Stat label="Shortlisted" value={metrics.shortlisted_count} /></Grid>
              <Grid item xs={12} sm={6} md={3}><Stat label="Hired" value={metrics.hired_count} /></Grid>
              <Grid item xs={12} sm={6} md={3}><Stat label="Rejected" value={metrics.rejected_count} /></Grid>
              <Grid item xs={12} sm={6} md={3}><Stat label="Avg. time-to-hire" value={`${metrics.average_time_to_hire_days ?? 0} days`} /></Grid>
              <Grid item xs={12} sm={6} md={3}><Stat label="Offer acceptance" value={`${metrics.offer_acceptance_rate ?? 0}%`} /></Grid>
              <Grid item xs={12} sm={6} md={3}><Stat label="Evaluations submitted" value={metrics.interviewer_evaluation_count} /></Grid>
            </Grid>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <ChartCard title="Applications by status" description="Current application counts grouped by backend status.">
                  {applicationsByStatusChart.labels?.length ? <Bar data={applicationsByStatusChart} options={barChartOptions} /> : <Typography color="text.secondary">No status data yet.</Typography>}
                </ChartCard>
              </Grid>
              <Grid item xs={12} md={6}>
                <ChartCard title="Candidate funnel" description="Candidates moving through key recruitment stages.">
                  {candidateFunnelChart ? <Bar data={candidateFunnelChart} options={barChartOptions} /> : <Typography color="text.secondary">No funnel data yet.</Typography>}
                </ChartCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <ChartCard title="Time-to-hire" description="Average number of days from application to hired.">
                  <Bar data={timeToHireChart} options={barChartOptions} />
                </ChartCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <ChartCard title="Offer acceptance rate" description="Accepted offers compared with total sent offers.">
                  <Doughnut data={offerAcceptanceChart} options={compactChartOptions} />
                </ChartCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <ChartCard title="Recruiter performance" description="Simple summary of hires and completed evaluation inputs.">
                  <Bar data={performanceChart} options={barChartOptions} />
                </ChartCard>
              </Grid>
            </Grid>
          </Stack>
        )}
      </Paper>
    </Box>
  );
}
