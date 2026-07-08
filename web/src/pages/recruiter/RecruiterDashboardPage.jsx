import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getApplications, getJobs, getNotifications, getRecruiterAnalytics } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage, titleize } from './recruiterUtils.js';

function StatCard({ label, value, helper, tone = 'primary' }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack spacing={1}>
          <Typography color="text.secondary" variant="body2">{label}</Typography>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>{value ?? 0}</Typography>
          {helper ? <Chip color={tone} label={helper} size="small" variant="outlined" sx={{ alignSelf: 'flex-start' }} /> : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

function StatusRow({ label, count, total }) {
  const percent = total ? Math.round((count / total) * 100) : 0;
  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
        <Typography variant="body2">{titleize(label)}</Typography>
        <Typography color="text.secondary" variant="body2">{count} • {percent}%</Typography>
      </Stack>
      <LinearProgress value={percent} variant="determinate" sx={{ height: 8, borderRadius: 999 }} />
    </Box>
  );
}

function CandidateRow({ application }) {
  const applicantName = application.applicant_name ?? application.candidate_name ?? application.applicant?.full_name ?? 'Candidate';
  const jobTitle = application.job_title ?? application.job?.title ?? 'Job not assigned';
  const score = application.final_score ?? application.ai_score ?? application.screening_score;
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
      <Box>
        <Typography sx={{ fontWeight: 700 }}>{applicantName}</Typography>
        <Typography color="text.secondary" variant="body2">{jobTitle} • {titleize(application.status)}</Typography>
      </Box>
      <Stack alignItems={{ xs: 'flex-start', md: 'flex-end' }}>
        <Chip label={score === undefined || score === null ? 'AI score pending' : `AI score ${score}`} size="small" variant="outlined" />
      </Stack>
    </Stack>
  );
}

export default function RecruiterDashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [unreadNotifications, setUnreadNotifications] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getRecruiterAnalytics(), getJobs(), getApplications(), getNotifications()])
      .then(([analyticsResult, jobsResult, applicationsResult, notificationsResult]) => {
        if (!active) return;
        if (analyticsResult.status === 'fulfilled') setAnalytics(analyticsResult.value);
        if (jobsResult.status === 'fulfilled') setJobs(jobsResult.value);
        if (applicationsResult.status === 'fulfilled') setApplications(applicationsResult.value);
        if (notificationsResult.status === 'fulfilled') setUnreadNotifications(notificationsResult.value.filter((item) => !item.is_read));
        if (analyticsResult.status === 'rejected' && jobsResult.status === 'rejected') setError(getApiErrorMessage(analyticsResult.reason, 'Unable to load recruiter dashboard.'));
      })
      .finally(() => active && setIsLoading(false));
    return () => { active = false; };
  }, []);

  const metrics = analytics?.metrics ?? analytics ?? {};
  const statusBreakdown = useMemo(() => applications.reduce((acc, application) => {
    acc[application.status] = (acc[application.status] ?? 0) + 1;
    return acc;
  }, {}), [applications]);
  const pendingScreening = applications.filter((application) => ['submitted', 'screened'].includes(application.status)).length;
  const activeJobs = jobs.filter((job) => ['open', 'published', 'active'].includes(job.status)).length;
  const upcomingWork = applications.filter((application) => ['screened', 'shortlisted', 'interview_scheduled', 'interview_completed'].includes(application.status)).slice(0, 5);
  const totalApplications = metrics.total_applications ?? applications.length;

  return (
    <Box>
      <RecruiterNav />
      <Stack spacing={3}>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
          <Box>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>Recruiter Dashboard</Typography>
            <Typography color="text.secondary">Manage job demand, screening queues, candidate movement, and recruiter follow-up actions.</Typography>
          </Box>
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            <Button component={RouterLink} to="/recruiter/jobs/create" variant="contained">Create job</Button>
            <Button component={RouterLink} to="/recruiter/analytics" variant="outlined">View analytics</Button>
          </Stack>
        </Stack>
        {error ? <Alert severity="error">{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading recruiter dashboard" /> : null}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Jobs" value={metrics.total_job_postings ?? jobs.length} helper={`${activeJobs} active`} /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Applications" value={totalApplications} helper="Total pipeline" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Pending screening" value={pendingScreening} helper="Needs review" tone={pendingScreening ? 'warning' : 'success'} /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Unread notifications" value={unreadNotifications.length} helper="Follow-up" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Shortlisted" value={metrics.shortlisted_count ?? statusBreakdown.shortlisted} helper="Interview-ready" tone="success" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Hired" value={metrics.hired_count ?? statusBreakdown.hired} helper="Closed roles" tone="success" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Avg. time-to-hire" value={`${metrics.average_time_to_hire_days ?? 0} days`} helper="Cycle speed" /></Grid>
          <Grid item xs={12} sm={6} md={3}><StatCard label="Offer acceptance" value={`${metrics.offer_acceptance_rate ?? 0}%`} helper="Candidate closing" tone="success" /></Grid>
        </Grid>

        <Grid container spacing={2}>
          <Grid item xs={12} md={5}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography component="h3" variant="h6">Application status mix</Typography>
                <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>Live distribution from applications currently visible to you.</Typography>
                <Stack spacing={2}>
                  {Object.entries(statusBreakdown).slice(0, 6).map(([status, count]) => <StatusRow key={status} label={status} count={count} total={applications.length} />)}
                  {!applications.length ? <Typography color="text.secondary">No applications yet. Publish or share a job to start the funnel.</Typography> : null}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={7}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
                  <Box>
                    <Typography component="h3" variant="h6">Priority candidate queue</Typography>
                    <Typography color="text.secondary" variant="body2">Candidates ready for screening, interview coordination, or hiring decision preparation.</Typography>
                  </Box>
                  <Button component={RouterLink} to="/recruiter/applications" variant="outlined">Open applications</Button>
                </Stack>
                <Divider sx={{ my: 2 }} />
                <Stack spacing={1.5} divider={<Divider flexItem />}>
                  {upcomingWork.map((application) => <CandidateRow key={application.id} application={application} />)}
                  {!upcomingWork.length ? <Typography color="text.secondary">No priority candidates at the moment.</Typography> : null}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography component="h3" variant="h6">Recruiter quick actions</Typography>
                <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>Common next steps for moving candidates through the human-led recruitment process.</Typography>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  <Button component={RouterLink} to="/recruiter/jobs" variant="outlined">Review job rankings</Button>
                  <Button component={RouterLink} to="/recruiter/applications" variant="outlined">Assign interviews</Button>
                  <Button component={RouterLink} to="/recruiter/hiring-decisions" variant="outlined">Prepare decisions</Button>
                  <Button component={RouterLink} to="/recruiter/notifications" variant="outlined">Check notifications</Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
