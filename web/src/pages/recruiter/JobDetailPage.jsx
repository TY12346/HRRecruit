import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Grid, List, ListItem, ListItemText, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { closeJobApplicationIntake, getJob, getJobCandidateComparison, getRankedCandidates } from '../../api/client.js';
import { formatJobDescriptionText } from '../../utils/jobDescriptionFormatting.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage, titleize } from './recruiterUtils.js';

export default function JobDetailPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [ranked, setRanked] = useState([]);
  const [readiness, setReadiness] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getJob(jobId), getRankedCandidates(jobId), getJobCandidateComparison(jobId)]).then(([jobResult, rankedResult, comparisonResult]) => {
      if (!active) return;
      if (jobResult.status === 'fulfilled') setJob(jobResult.value); else setError(getApiErrorMessage(jobResult.reason, 'Unable to load job.'));
      if (rankedResult.status === 'fulfilled') setRanked(rankedResult.value);
      if (comparisonResult.status === 'fulfilled') setReadiness(comparisonResult.value.readiness);
    }).finally(() => active && setIsLoading(false));
    return () => { active = false; };
  }, [jobId]);

  const closeIntake = async () => {
    setError('');
    try {
      const result = await closeJobApplicationIntake(jobId);
      setJob(result.job);
      setReadiness(result.readiness);
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to close application intake.')); }
  };

  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}>
    {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
    {isLoading ? <CircularProgress /> : null}
    {job ? <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
        <Box><Typography variant="h5" sx={{ fontWeight: 700 }}>{job.title}</Typography><Typography color="text.secondary">{job.organization_name} • {job.location}</Typography><Chip label={titleize(job.status)} color={job.status === 'open' ? 'success' : 'default'} sx={{ mt: 1 }} /></Box>
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/edit`} variant="contained">Edit</Button>
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/requirements`} variant="outlined">Requirements</Button>
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/scorecard`} variant="outlined">Evaluation scorecard</Button>
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/ranking`} variant="outlined">Qualified ranking</Button>
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/hiring-recommendation`} variant="outlined">Candidate comparison</Button>
          {job.status === 'open' ? <Button color="warning" onClick={closeIntake} variant="contained">Close application intake</Button> : null}
        </Stack>
      </Stack>
      {readiness && !readiness.ready ? <Alert severity="info">Hiring recommendation is not ready: {readiness.reasons.join(' ')}</Alert> : null}
      {readiness?.ready ? <Alert severity="success">Ready for Hiring Recommendation.</Alert> : null}
      <Typography sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{formatJobDescriptionText(job.description)}</Typography>
      <Grid container spacing={2}><Grid item xs={12} md={4}><Card><CardContent><Typography color="text.secondary">Qualified candidates</Typography><Typography variant="h4">{ranked.length}</Typography></CardContent></Card></Grid><Grid item xs={12} md={4}><Card><CardContent><Typography color="text.secondary">Vacancies</Typography><Typography variant="h4">{job.vacancies}</Typography></CardContent></Card></Grid><Grid item xs={12} md={4}><Card><CardContent><Typography color="text.secondary">Employment</Typography><Typography>{job.employment_type}</Typography><Typography>{job.approximate_salary}</Typography></CardContent></Card></Grid></Grid>
      <Box><Typography variant="h6">Requirements</Typography><List>{job.requirements?.map((req) => <ListItem key={req.id}><ListItemText primary={`${titleize(req.requirement_type)} (${req.weight_score})`} secondary={`${req.description} • Threshold ${req.minimum_threshold}`} /></ListItem>)}{!job.requirements?.length ? <ListItem><ListItemText primary="No requirements configured." /></ListItem> : null}</List></Box>
    </Stack> : null}
  </Paper></Box>;
}
