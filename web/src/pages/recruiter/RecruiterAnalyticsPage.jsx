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

function SankeyChart({ data }) {
  const width = 1040;
  const height = 320;
  const nodeWidth = 132;
  const nodeHeight = 42;
  const columnGap = (width - 36 - nodeWidth) / 5;
  const nodesByColumn = new Map();

  data.nodes.forEach((node) => {
    const columnNodes = nodesByColumn.get(node.column) ?? [];
    columnNodes.push(node);
    nodesByColumn.set(node.column, columnNodes);
  });

  const positions = new Map();
  nodesByColumn.forEach((nodes, column) => {
    const gap = 24;
    const groupHeight = (nodes.length * nodeHeight) + ((nodes.length - 1) * gap);
    nodes.forEach((node, index) => {
      positions.set(node.id, {
        x: 18 + (column * columnGap),
        y: ((height - groupHeight) / 2) + (index * (nodeHeight + gap)),
      });
    });
  });

  const outgoing = new Map();
  const incoming = new Map();
  data.links.forEach((link) => {
    outgoing.set(link.source, [...(outgoing.get(link.source) ?? []), link]);
    incoming.set(link.target, [...(incoming.get(link.target) ?? []), link]);
  });
  const nodeValues = new Map(data.nodes.map((node) => {
    const incomingTotal = (incoming.get(node.id) ?? []).reduce((total, link) => total + link.value, 0);
    const outgoingTotal = (outgoing.get(node.id) ?? []).reduce((total, link) => total + link.value, 0);
    return [node.id, Math.max(incomingTotal, outgoingTotal)];
  }));
  const nodeMap = new Map(data.nodes.map((node) => [node.id, node]));
  const anchorOffset = (links, link) => (links.indexOf(link) - ((links.length - 1) / 2)) * 10;

  return (
    <Box sx={{ width: '100%', height: '100%', overflowX: 'auto' }}>
      <svg
        aria-label={`Applicant pipeline flow for ${data.total} applications`}
        role="img"
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: 'block', minWidth: 680, width: '100%', height: '100%' }}
      >
        <title>Applicant pipeline Sankey chart</title>
        {data.links.map((link) => {
          const source = positions.get(link.source);
          const target = positions.get(link.target);
          const sourceY = source.y + (nodeHeight / 2) + anchorOffset(outgoing.get(link.source), link);
          const targetY = target.y + (nodeHeight / 2) + anchorOffset(incoming.get(link.target), link);
          const sourceX = source.x + nodeWidth;
          const targetX = target.x;
          const curve = (targetX - sourceX) * 0.48;
          const path = `M ${sourceX} ${sourceY} C ${sourceX + curve} ${sourceY}, ${targetX - curve} ${targetY}, ${targetX} ${targetY}`;
          return (
            <path
              d={path}
              fill="none"
              key={`${link.source}-${link.target}`}
              opacity="0.42"
              stroke={nodeMap.get(link.source)?.color ?? '#3b82f6'}
              strokeLinecap="round"
              strokeWidth={Math.max(4, (link.value / data.total) * 30)}
            >
              <title>{`${nodeMap.get(link.source)?.label} → ${nodeMap.get(link.target)?.label}: ${link.value}`}</title>
            </path>
          );
        })}
        {data.nodes.map((node) => {
          const position = positions.get(node.id);
          return (
            <g key={node.id} transform={`translate(${position.x} ${position.y})`}>
              <rect fill={node.color} height={nodeHeight} rx="8" width={nodeWidth} />
              <text fill="#fff" fontSize="12" fontWeight="600" textAnchor="middle" x={nodeWidth / 2} y="17">
                {node.label}
              </text>
              <text fill="#fff" fontSize="12" opacity="0.9" textAnchor="middle" x={nodeWidth / 2} y="33">
                {`${nodeValues.get(node.id) ?? 0} applicant${nodeValues.get(node.id) === 1 ? '' : 's'}`}
              </text>
            </g>
          );
        })}
      </svg>
    </Box>
  );
}

function hasSankeyData(data) {
  return Boolean(data?.total > 0 && data.nodes?.length && data.links?.length);
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
  const applicantPipelineSankey = charts.applicant_pipeline_sankey;
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

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'minmax(320px, 1fr) minmax(680px, 2fr)' }, gap: 2 }}>
              <ChartCard title="Applications by status" description="Current application counts grouped by backend status.">
                {hasChartData(applicationsByStatusChart) ? <Bar data={applicationsByStatusChart} options={barChartOptions} /> : <EmptyChart>No application status data yet.</EmptyChart>}
              </ChartCard>
              <ChartCard title="Applicant pipeline flow" description="Follow applicants from review through interviews, evaluations, offers, and hiring outcomes.">
                {hasSankeyData(applicantPipelineSankey) ? <SankeyChart data={applicantPipelineSankey} /> : <EmptyChart>No pipeline flow data yet.</EmptyChart>}
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
