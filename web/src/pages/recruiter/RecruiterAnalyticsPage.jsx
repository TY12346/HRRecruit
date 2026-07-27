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
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { downloadAnalyticsReportPdf, getRecruiterAnalytics } from '../../api/client.js';
import {
  barChartOptions,
  chartFromMap,
  chartHeight,
  compactChartOptions,
  downloadBlob,
  horizontalBarChartOptions,
  percentageDoughnut,
  singleValueBar,
} from '../analytics/analyticsChartUtils.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage, titleize } from './recruiterUtils.js';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function Stat({ label, value }) {
  return (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
      <Box sx={{ position: 'absolute', inset: '0 auto 0 0', width: 4, bgcolor: 'primary.main' }} />
      <CardContent sx={{ pl: 2 }}>
        <Typography color="text.secondary" variant="body2">{label}</Typography>
        <Typography component="p" variant="h4" sx={{ fontWeight: 700, mt: 0.5 }}>{value ?? 0}</Typography>
      </CardContent>
    </Card>
  );
}

function EmptyChart({ children }) {
  return (
    <Stack alignItems="center" justifyContent="center" sx={{ height: '100%', minHeight: 180, textAlign: 'center', px: 2 }}>
      <Box
        aria-hidden="true"
        sx={{ width: 44, height: 32, mb: 1.5, borderBottom: '2px solid', borderLeft: '2px solid', borderColor: 'primary.light', opacity: 0.8 }}
      />
      <Typography color="text.secondary" variant="body2">{children}</Typography>
    </Stack>
  );
}

function hasChartData(chart) {
  return Boolean(
    chart?.labels?.length
    && chart.datasets?.some((dataset) => dataset.data?.some((value) => Number(value) > 0)),
  );
}

const dashboardGrid = (minWidth) => ({
  display: 'grid',
  gridTemplateColumns: `repeat(auto-fit, minmax(min(100%, ${minWidth}px), 1fr))`,
  gap: 2,
});

function InsightsCard({ pipelineHealth }) {
  const insights = pipelineHealth?.insights ?? [];
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography component="h3" variant="h6">Pipeline health insights</Typography>
        <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>
          Highlights bottlenecks and conversion risks for recruiter follow-up.
        </Typography>
        <Stack spacing={1}>
          <Typography variant="body2"><strong>Bottleneck:</strong> {pipelineHealth?.bottleneck_stage ?? 'Not enough data'} ({pipelineHealth?.bottleneck_count ?? 0})</Typography>
          <Typography variant="body2"><strong>Highest drop-off:</strong> {pipelineHealth?.highest_dropout_status ?? 'None yet'} ({pipelineHealth?.highest_dropout_count ?? 0})</Typography>
          {insights.map((insight) => <Alert key={insight} severity="info">{insight}</Alert>)}
        </Stack>
      </CardContent>
    </Card>
  );
}

function TopJobsTable({ rows }) {
  return (
    <Card>
      <CardContent>
        <Typography component="h3" variant="h6" sx={{ mb: 2 }}>Top jobs by application volume</Typography>
        <Box sx={{ overflowX: 'auto' }}>
          <Table size="small" sx={{ minWidth: 560 }}>
            <TableHead>
              <TableRow>
                <TableCell>Job</TableCell>
                <TableCell>Applications</TableCell>
                <TableCell>Hires</TableCell>
                <TableCell>Avg. AI score</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(rows ?? []).map((row) => (
                <TableRow key={row.job_id}>
                  <TableCell>{row.job_title}</TableCell>
                  <TableCell>{row.applications}</TableCell>
                  <TableCell>{row.hires}</TableCell>
                  <TableCell>{row.average_score ?? '—'}</TableCell>
                </TableRow>
              ))}
              {!(rows ?? []).length ? <TableRow><TableCell colSpan={4}>No job-level analytics yet.</TableCell></TableRow> : null}
            </TableBody>
          </Table>
        </Box>
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, description, children, height = 280 }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography component="h3" variant="h6">{title}</Typography>
        {description ? <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>{description}</Typography> : null}
        <Box sx={{ ...chartHeight, height }}>{children}</Box>
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
  const applicantFunnelChart = charts.applicant_funnel;
  const timeToHireChart = singleValueBar('Average time-to-hire', metrics.average_time_to_hire_days, 'Days', '#7c3aed');
  const offerAcceptanceChart = percentageDoughnut('Accepted offers', metrics.offer_acceptance_rate, '#16a34a');
  const conversionRatesChart = charts.conversion_rates;
  const scoreDistributionChart = charts.score_distribution;
  const applicationsOverTimeChart = charts.applications_over_time;
  const topJobsChart = charts.top_jobs_by_applications;
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
  const hasAnalytics = Number(metrics.total_job_postings) > 0 || Number(metrics.total_applications) > 0;

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: { xs: 2, md: 3 } }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" gap={2} sx={{ mb: 2 }}>
          <Box>
            <Typography component="h1" variant="h5" sx={{ fontWeight: 700 }}>Recruiter analytics</Typography>
            <Typography color="text.secondary" variant="body2" sx={{ mt: 0.5 }}>
              Track your jobs, applicant pipeline, and hiring outcomes
              {analytics?.organization?.name ? ` for ${analytics.organization.name}` : ''}.
            </Typography>
          </Box>
          <Button variant="outlined" onClick={handleExportPdf} disabled={isExporting || isLoading}>
            {isExporting ? 'Exporting…' : 'Export PDF'}
          </Button>
        </Stack>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? (
          <Stack alignItems="center" justifyContent="center" sx={{ minHeight: 320 }}>
            <CircularProgress aria-label="Loading recruiter analytics" />
          </Stack>
        ) : (
          <Stack spacing={3}>
            {!hasAnalytics ? (
              <Alert severity="info">
                Analytics will populate as soon as you publish a job and applicants enter your pipeline.
              </Alert>
            ) : null}

            <Box sx={dashboardGrid(190)}>
              <Stat label="Job postings" value={metrics.total_job_postings} />
              <Stat label="Applications" value={metrics.total_applications} />
              <Stat label="Under review" value={metrics.shortlisted_count} />
              <Stat label="Hired" value={metrics.hired_count} />
              <Stat label="Rejected" value={metrics.rejected_count} />
              <Stat label="Avg. time-to-hire" value={`${metrics.average_time_to_hire_days ?? 0} days`} />
              <Stat label="Offer acceptance" value={`${metrics.offer_acceptance_rate ?? 0}%`} />
              <Stat label="Evaluations submitted" value={metrics.interviewer_evaluation_count} />
            </Box>

            <Box sx={dashboardGrid(420)}>
                <ChartCard title="Applications by status" description="Current application counts grouped by backend status.">
                  {hasChartData(applicationsByStatusChart) ? <Bar data={applicationsByStatusChart} options={barChartOptions} /> : <EmptyChart>No application status data yet.</EmptyChart>}
                </ChartCard>
                <ChartCard title="Applicant funnel" description="Applicants moving through key recruitment stages.">
                  {hasChartData(applicantFunnelChart) ? <Bar data={applicantFunnelChart} options={barChartOptions} /> : <EmptyChart>No funnel data yet.</EmptyChart>}
                </ChartCard>
            </Box>

            <Box sx={dashboardGrid(300)}>
                <ChartCard title="Time-to-hire" description="Average number of days from application to hired.">
                  {Number(metrics.average_time_to_hire_days) > 0 ? <Bar data={timeToHireChart} options={barChartOptions} /> : <EmptyChart>No completed hires to calculate this metric.</EmptyChart>}
                </ChartCard>
                <ChartCard title="Offer acceptance rate" description="Accepted offers compared with total sent offers.">
                  {Number(metrics.total_offers) > 0 ? <Doughnut data={offerAcceptanceChart} options={compactChartOptions} /> : <EmptyChart>No offers have been sent yet.</EmptyChart>}
                </ChartCard>
                <ChartCard title="Recruiter performance" description="Simple summary of hires and completed evaluation inputs.">
                  {hasChartData(performanceChart) ? <Bar data={performanceChart} options={barChartOptions} /> : <EmptyChart>Performance data will appear after hires or evaluations.</EmptyChart>}
                </ChartCard>
            </Box>

            <Box sx={dashboardGrid(420)}>
                <ChartCard title="Conversion rates" description="Percentage of applicants reaching each recruitment milestone.">
                  {hasChartData(conversionRatesChart) ? <Bar data={conversionRatesChart} options={barChartOptions} /> : <EmptyChart>No conversion data yet.</EmptyChart>}
                </ChartCard>
                <ChartCard title="AI score distribution" description="Distribution of applicants by final AI screening score band.">
                  {hasChartData(scoreDistributionChart) ? <Doughnut data={scoreDistributionChart} options={compactChartOptions} /> : <EmptyChart>No screening score data yet.</EmptyChart>}
                </ChartCard>
                <ChartCard title="Applications over time" description="Monthly application volume for the recruiter pipeline.">
                  {hasChartData(applicationsOverTimeChart) ? <Bar data={applicationsOverTimeChart} options={barChartOptions} /> : <EmptyChart>No timeline data yet.</EmptyChart>}
                </ChartCard>
                <ChartCard title="Top jobs by volume" description="Jobs receiving the most applications.">
                  {hasChartData(topJobsChart) ? <Bar data={topJobsChart} options={horizontalBarChartOptions} /> : <EmptyChart>No job analytics yet.</EmptyChart>}
                </ChartCard>
                <InsightsCard pipelineHealth={metrics.pipeline_health} />
            </Box>

            <TopJobsTable rows={analytics?.top_jobs_by_applications ?? []} />
          </Stack>
        )}
      </Paper>
    </Box>
  );
}
