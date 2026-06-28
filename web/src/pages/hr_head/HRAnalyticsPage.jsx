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
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { downloadAnalyticsReportPdf, getOrganizationAnalyticsOverview } from '../../api/client.js';
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
import HRHeadNav from './HRHeadNav.jsx';
import { getApiErrorMessage, titleize } from './hrHeadUtils.js';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function MetricCard({ label, value }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography color="text.secondary" variant="body2">{label}</Typography>
        <Typography component="p" variant="h4" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography>
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


function InsightsCard({ pipelineHealth }) {
  const insights = pipelineHealth?.insights ?? [];
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography component="h3" variant="h6">Pipeline health insights</Typography>
        <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>
          Uses conversion, drop-off, and bottleneck signals to highlight where HR should investigate.
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
        <Table>
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
                <TableCell>{row.average_score}</TableCell>
              </TableRow>
            ))}
            {!(rows ?? []).length ? <TableRow><TableCell colSpan={4}>No job-level analytics yet.</TableCell></TableRow> : null}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function PerformanceTable({ rows, type }) {
  const isRecruiter = type === 'recruiter';
  return (
    <Card>
      <CardContent>
        <Typography component="h3" variant="h6" sx={{ mb: 2 }}>
          {isRecruiter ? 'Recruiter performance details' : 'Interviewer performance details'}
        </Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              {isRecruiter ? (
                <>
                  <TableCell>Jobs</TableCell>
                  <TableCell>Applications</TableCell>
                  <TableCell>Hires</TableCell>
                </>
              ) : (
                <>
                  <TableCell>Assigned interviews</TableCell>
                  <TableCell>Completed interviews</TableCell>
                  <TableCell>Evaluations</TableCell>
                  <TableCell>Average score</TableCell>
                </>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={isRecruiter ? row.recruiter_id : row.interviewer_id}>
                <TableCell>{isRecruiter ? row.recruiter_name : row.interviewer_name}</TableCell>
                {isRecruiter ? (
                  <>
                    <TableCell>{row.job_postings}</TableCell>
                    <TableCell>{row.applications}</TableCell>
                    <TableCell>{row.hire_count}</TableCell>
                  </>
                ) : (
                  <>
                    <TableCell>{row.assigned_interviews}</TableCell>
                    <TableCell>{row.completed_interviews}</TableCell>
                    <TableCell>{row.evaluation_count}</TableCell>
                    <TableCell>{row.average_evaluation_score}</TableCell>
                  </>
                )}
              </TableRow>
            ))}
            {!rows.length ? (
              <TableRow><TableCell colSpan={isRecruiter ? 4 : 5}>No performance data yet.</TableCell></TableRow>
            ) : null}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export default function HRAnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadAnalytics = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getOrganizationAnalyticsOverview();
        if (isMounted) setAnalytics(data);
      } catch (loadError) {
        if (isMounted) setError(getApiErrorMessage(loadError, 'Unable to load HR analytics.'));
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadAnalytics();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleExportPdf = async () => {
    setIsExporting(true);
    setError('');
    try {
      const pdfBlob = await downloadAnalyticsReportPdf('hr_head');
      downloadBlob(pdfBlob, 'hr-head-summary.pdf');
    } catch (exportError) {
      setError(getApiErrorMessage(exportError, 'Unable to export HR analytics PDF.'));
    } finally {
      setIsExporting(false);
    }
  };

  const metrics = analytics?.metrics ?? {};
  const charts = analytics?.charts ?? {};
  const applicationsByStatus = metrics.applications_by_status ?? {};
  const applicationsByStatusChart = charts.applications_by_status ?? chartFromMap(applicationsByStatus, 'Applications', titleize);
  const timeToHireChart = singleValueBar('Average time-to-hire', metrics.average_time_to_hire_days, 'Days', '#7c3aed');
  const offerAcceptanceChart = percentageDoughnut('Accepted offers', metrics.offer_acceptance_rate, '#16a34a');
  const conversionRatesChart = charts.conversion_rates;
  const scoreDistributionChart = charts.score_distribution;
  const applicationsOverTimeChart = charts.applications_over_time;
  const topJobsChart = charts.top_jobs_by_applications;

  return (
    <Box>
      <HRHeadNav />
      <Stack spacing={3}>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" gap={2}>
          <Box>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>HR Analytics</Typography>

          </Box>
          <Button variant="outlined" onClick={handleExportPdf} disabled={isExporting || isLoading}>
            {isExporting ? 'Exporting…' : 'Export PDF'}
          </Button>
        </Stack>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading HR analytics" /> : null}

        {analytics?.organization ? <Alert severity="info">Viewing analytics for {analytics.organization.name}.</Alert> : null}

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}><MetricCard label="Job postings" value={metrics.total_job_postings} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard label="Applications" value={metrics.total_applications} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard label="Shortlisted" value={metrics.shortlisted_count} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard label="Hired" value={metrics.hired_count} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard label="Hiring success" value={`${metrics.hiring_success_rate ?? 0}%`} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard label="Rejection rate" value={`${metrics.rejection_rate ?? 0}%`} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard label="Dropout rate" value={`${metrics.dropout_rate ?? 0}%`} /></Grid>
          <Grid item xs={12} sm={6} md={3}><MetricCard label="Offer acceptance" value={`${metrics.offer_acceptance_rate ?? 0}%`} /></Grid>
        </Grid>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <ChartCard title="Applications by status" description="Organization application totals grouped by status.">
              {applicationsByStatusChart.labels?.length ? <Bar data={applicationsByStatusChart} options={barChartOptions} /> : <Typography color="text.secondary">No status data yet.</Typography>}
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="Candidate funnel" description="Candidates across the end-to-end recruitment funnel.">
              {charts.candidate_funnel ? <Bar data={charts.candidate_funnel} options={barChartOptions} /> : <Typography color="text.secondary">No funnel data yet.</Typography>}
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={4}>
            <ChartCard title="Time-to-hire" description="Average days from application to hired status.">
              <Bar data={timeToHireChart} options={barChartOptions} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={4}>
            <ChartCard title="Offer acceptance rate" description="Accepted offers compared with total offers.">
              <Doughnut data={offerAcceptanceChart} options={compactChartOptions} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={4}>
            <ChartCard title="Recruiter performance" description="Jobs, applications, and hires per recruiter.">
              {charts.recruiter_performance ? <Bar data={charts.recruiter_performance} options={horizontalBarChartOptions} /> : <Typography color="text.secondary">No recruiter performance data yet.</Typography>}
            </ChartCard>
          </Grid>
          <Grid item xs={12}>
            <ChartCard title="Interviewer performance" description="Assigned interviews, completed interviews, and submitted evaluations.">
              {charts.interviewer_performance ? <Bar data={charts.interviewer_performance} options={barChartOptions} /> : <Typography color="text.secondary">No interviewer performance data yet.</Typography>}
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="Conversion rates" description="Percentage of candidates reaching each recruitment milestone.">
              {conversionRatesChart ? <Bar data={conversionRatesChart} options={barChartOptions} /> : <Typography color="text.secondary">No conversion data yet.</Typography>}
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="AI score distribution" description="Distribution of candidates by final AI screening score band.">
              {scoreDistributionChart ? <Doughnut data={scoreDistributionChart} options={compactChartOptions} /> : <Typography color="text.secondary">No screening score data yet.</Typography>}
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="Applications over time" description="Monthly application volume across the organization.">
              {applicationsOverTimeChart ? <Bar data={applicationsOverTimeChart} options={barChartOptions} /> : <Typography color="text.secondary">No timeline data yet.</Typography>}
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard title="Top jobs by volume" description="Jobs receiving the most applications.">
              {topJobsChart ? <Bar data={topJobsChart} options={horizontalBarChartOptions} /> : <Typography color="text.secondary">No job analytics yet.</Typography>}
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <InsightsCard pipelineHealth={metrics.pipeline_health} />
          </Grid>
        </Grid>

        <TopJobsTable rows={analytics?.top_jobs_by_applications ?? []} />
        <PerformanceTable rows={analytics?.recruiter_performance ?? []} type="recruiter" />
        <PerformanceTable rows={analytics?.interviewer_performance ?? []} type="interviewer" />
      </Stack>
    </Box>
  );
}
