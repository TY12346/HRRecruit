import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, Paper, Stack, Table, TableBody, TableCell, TableRow, Typography } from '@mui/material';
import { Link as RouterLink, useParams, useSearchParams } from 'react-router-dom';
import { getJobApplicantComparison } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage, scoreText } from './recruiterUtils.js';

const ListValue = ({ values }) => values?.length
  ? <Stack direction="row" gap={0.75} flexWrap="wrap">{values.map((value) => <Chip key={value} label={value} size="small" />)}</Stack>
  : '—';

export default function ApplicantComparisonPage() {
  const { jobId } = useParams();
  const [searchParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const applicationIds = useMemo(() => [...new Set(
    (searchParams.get('applications') || '').split(',').filter(Boolean).map(Number).filter(Number.isInteger),
  )], [searchParams]);

  useEffect(() => {
    if (applicationIds.length < 2 || applicationIds.length > 3) return;
    getJobApplicantComparison(jobId)
      .then(setData)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load applicant comparison.')));
  }, [jobId, applicationIds]);

  const applicants = data?.applicants.filter((applicant) => applicationIds.includes(applicant.application_id)) || [];
  const invalidSelection = applicationIds.length < 2 || applicationIds.length > 3;
  const rows = data ? [
    ['AI match score', (applicant) => scoreText(applicant.ai_resume_score)],
    ['Matched skills', (applicant) => <ListValue values={applicant.matched_skills} />],
    ['Missing skills', (applicant) => <ListValue values={applicant.missing_skills} />],
    ['AI interview summary', (applicant) => applicant.ai_interview_summaries?.join('\n\n') || '—'],
    ['Interviewer remarks', (applicant) => applicant.interviewer_remarks?.join('\n\n') || '—'],
    ['Interview evidence', (applicant) => applicant.interviews?.length ? `${applicant.interviews.length} interview evaluation${applicant.interviews.length === 1 ? '' : 's'}` : '—'],
  ] : [];

  return <Box><RecruiterNav /><Paper sx={{ p: { xs: 2, md: 3 } }}><Stack spacing={2.5}>
    <Button
      aria-label="Back to hiring decision"
      component={RouterLink}
      to={`/recruiter/jobs/${jobId}/hiring-decision`}
      variant="outlined"
      sx={{ alignSelf: 'flex-start' }}
    >
      ← Back
    </Button>
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700 }}>Compare selected applicants</Typography>
      <Typography color="text.secondary">Review applicant evidence side by side. This comparison supports, but does not replace, your hiring decision.</Typography>
    </Box>
    {invalidSelection ? <Alert severity="warning">Select no less than 2 and no more than 3 applicants to compare.</Alert> : null}
    {error ? <Alert severity="error">{error}</Alert> : null}
    {!invalidSelection && !data && !error ? <CircularProgress /> : null}
    {data && applicants.length !== applicationIds.length ? <Alert severity="error">One or more selected applicants are unavailable for this job.</Alert> : null}
    {data && applicants.length === applicationIds.length ? <>
      <Typography><strong>{data.job.title}</strong> • Comparing {applicants.length} applicants</Typography>
      <Box sx={{ overflowX: 'auto' }}>
        <Table sx={{ minWidth: applicants.length === 3 ? 900 : 680, tableLayout: 'fixed', '& td': { verticalAlign: 'top', whiteSpace: 'pre-line' } }}>
          <TableBody>
            <TableRow sx={{ '& td': { bgcolor: 'primary.50' } }}>
              <TableCell sx={{ width: 180, fontWeight: 700 }}>Applicant</TableCell>
              {applicants.map((applicant) => <TableCell key={applicant.application_id}>
                <Typography sx={{ fontWeight: 700 }}>{applicant.applicant_name}</Typography>
                <Typography variant="body2" color="text.secondary">{applicant.applicant_email}</Typography>
                {applicant.applicant_phone ? <Typography variant="body2" color="text.secondary">{applicant.applicant_phone}</Typography> : null}
                {applicant.resume_url ? <Button size="small" component="a" href={applicant.resume_url} target="_blank" rel="noreferrer" sx={{ mt: 1 }}>View resume</Button> : null}
              </TableCell>)}
            </TableRow>
            {rows.map(([label, render]) => <TableRow key={label}>
              <TableCell component="th" scope="row" sx={{ fontWeight: 700 }}>{label}</TableCell>
              {applicants.map((applicant) => <TableCell key={applicant.application_id}>{render(applicant)}</TableCell>)}
            </TableRow>)}
          </TableBody>
        </Table>
      </Box>
    </> : null}
  </Stack></Paper></Box>;
}
