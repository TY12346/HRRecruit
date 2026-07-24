import { useEffect, useState } from 'react';
import { Box, Button, Card, CardContent, Chip, CircularProgress, Grid, List, ListItem, Paper, Stack, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { closeJobApplicationIntake, getJob, getJobApplicantComparison, getRankedApplicants } from '../../api/client.js';
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
    Promise.allSettled([getJob(jobId), getRankedApplicants(jobId), getJobApplicantComparison(jobId)]).then(([jobResult, rankedResult, comparisonResult]) => {
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

  const requirementsByType = ['skill', 'experience', 'education'].map((type) => ({
    type,
    items: (job?.requirements ?? []).filter((requirement) => requirement.requirement_type === type),
  }));

  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}>
    {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
    {isLoading ? <CircularProgress /> : null}
    {job ? <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'stretch', md: 'flex-start' }} spacing={2}>
        <Box><Typography variant="h5" sx={{ fontWeight: 700 }}>{job.title}</Typography><Typography color="text.secondary">{job.organization_name} • {job.location}</Typography><Chip label={titleize(job.status)} color={job.status === 'open' ? 'success' : 'default'} sx={{ mt: 1 }} /></Box>
        <Stack direction="row" alignItems="center" spacing={1} useFlexGap flexWrap="wrap">
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/edit`} variant="contained">Edit</Button>
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/requirements`} variant="outlined">Requirements</Button>
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/scorecard`} variant="outlined">Evaluation scorecard</Button>
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/ranking`} variant="outlined">View qualified applicants ranking</Button>
          <Button component={RouterLink} to={`/recruiter/jobs/${job.id}/hiring-decision`} variant="outlined">Make hiring decision</Button>
          {job.status === 'open' ? <Button color="warning" onClick={closeIntake} variant="contained">Close application intake</Button> : null}
        </Stack>
      </Stack>
      <Typography sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{formatJobDescriptionText(job.description)}</Typography>
      <Grid container spacing={2}><Grid item xs={12} md={4}><Card><CardContent><Typography color="text.secondary">Qualified applicants</Typography><Typography variant="h4">{ranked.length}</Typography></CardContent></Card></Grid><Grid item xs={12} md={4}><Card><CardContent><Typography color="text.secondary">Vacancies</Typography><Typography variant="h4">{job.vacancies}</Typography></CardContent></Card></Grid><Grid item xs={12} md={4}><Card><CardContent><Typography color="text.secondary">Employment</Typography><Typography>{titleize(job.employment_type)}</Typography></CardContent></Card></Grid></Grid>
      <Box>
        <Typography variant="h6">Requirements</Typography>
        {requirementsByType.filter(({ items }) => items.length > 0).map(({ type, items }) => (
          <Box key={type} sx={{ mt: 1.5 }}>
            <Typography sx={{ fontWeight: 600 }}>{titleize(type)}</Typography>
            <List sx={{ listStyleType: 'disc', pl: 3 }}>
              {items.map((requirement) => <ListItem key={requirement.id} sx={{ display: 'list-item', py: 0.25, pl: 0 }}>{requirement.description}</ListItem>)}
            </List>
          </Box>
        ))}
      </Box>
    </Stack> : null}
  </Paper></Box>;
}
