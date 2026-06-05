import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
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
import { getOrganizationAnalyticsOverview } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { getApiErrorMessage, titleize } from './hrHeadUtils.js';

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

function PerformanceTable({ rows, type }) {
  const isRecruiter = type === 'recruiter';
  return (
    <Card>
      <CardContent>
        <Typography component="h3" variant="h6" sx={{ mb: 2 }}>
          {isRecruiter ? 'Recruiter performance' : 'Interviewer performance'}
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

  useEffect(() => {
    let isMounted = true;

    const loadAnalytics = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getOrganizationAnalyticsOverview();
        if (isMounted) {
          setAnalytics(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, 'Unable to load HR analytics.'));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadAnalytics();

    return () => {
      isMounted = false;
    };
  }, []);

  const metrics = analytics?.metrics ?? {};
  const applicationsByStatus = metrics.applications_by_status ?? {};

  return (
    <Box>
      <HRHeadNav />
      <Stack spacing={3}>
        <Box>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
            HR Analytics
          </Typography>
          <Typography color="text.secondary">
            Organization-level hiring metrics, candidate funnel totals, and team performance.
          </Typography>
        </Box>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading HR analytics" /> : null}

        {analytics?.organization ? (
          <Alert severity="info">Viewing analytics for {analytics.organization.name}.</Alert>
        ) : null}

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

        <Card>
          <CardContent>
            <Typography component="h3" variant="h6" sx={{ mb: 2 }}>Applications by status</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Count</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(applicationsByStatus).map(([status, count]) => (
                  <TableRow key={status}>
                    <TableCell>{titleize(status)}</TableCell>
                    <TableCell>{count}</TableCell>
                  </TableRow>
                ))}
                {!Object.keys(applicationsByStatus).length ? (
                  <TableRow><TableCell colSpan={2}>No application status data yet.</TableCell></TableRow>
                ) : null}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <PerformanceTable rows={analytics?.recruiter_performance ?? []} type="recruiter" />
        <PerformanceTable rows={analytics?.interviewer_performance ?? []} type="interviewer" />
      </Stack>
    </Box>
  );
}
