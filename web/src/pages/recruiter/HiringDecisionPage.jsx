import { useEffect, useState } from 'react';
import { Box, Button, Checkbox, Chip, CircularProgress, FormControlLabel, Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getJobApplicantComparison, getJobHiringDecisions, submitJobHiringDecision } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { applicationName, formatDateTime, getApiErrorMessage, scoreText, titleize } from './recruiterUtils.js';

const nextStep = (decision) => {
  if (decision.status === 'pending_hr_approval') return 'Wait for the hiring manager to review this submission.';
  if (decision.status === 'rejected') return 'Review the hiring manager feedback and submit a revised decision if needed.';
  if (decision.decision_type === 'recommend_hire') return 'Create and send offers to the approved applicants.';
  return 'No offer action is required for this approved no-hire decision.';
};

export default function HiringDecisionPage() {
  const { jobId } = useParams();
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState([]);
  const [comparisonSelected, setComparisonSelected] = useState([]);
  const [noHire, setNoHire] = useState(false);
  const [justification, setJustification] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [pendingDecision, setPendingDecision] = useState(null);
  const [decisions, setDecisions] = useState([]);
  useEffect(() => {
    if (!jobId) return;
    Promise.all([getJobApplicantComparison(jobId), getJobHiringDecisions({ job_posting: jobId })])
      .then(([comparison, decisions]) => {
        setData(comparison);
        setDecisions(decisions);
        setPendingDecision(decisions.find((decision) => decision.status === 'pending_hr_approval') || null);
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load applicant comparison.')));
  }, [jobId]);
  const toggle = (id) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  const toggleComparison = (id) => {
    setComparisonSelected((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id);
      if (current.length >= 3) return current;
      return [...current, id];
    });
  };
  const submit = async () => {
    setError('');
    try {
      const result = await submitJobHiringDecision({ job_posting: Number(jobId), decision_type: noHire ? 'recommend_no_hire' : 'recommend_hire', application_ids: noHire ? [] : selected, justification });
      setPendingDecision(result);
      setDecisions((current) => [result, ...current.filter((decision) => decision.id !== result.id)]);
      setSuccess(`Hiring Decision #${result.id} submitted.`);
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to submit hiring decision.')); }
  };
  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}><Stack spacing={2}>
    <Typography variant="h5" sx={{ fontWeight: 700 }}>Job-level Hiring Decision</Typography>
    {error ? <Alert severity="error">{error}</Alert> : null}{success ? <Alert severity="success">{success}</Alert> : null}
    {!data ? <CircularProgress /> : <>
      <Typography><strong>{data.job.title}</strong> • {data.job.vacancies} vacancy/vacancies • {titleize(data.job.status)}</Typography>
      {pendingDecision ? <Alert severity="info">Hiring Decision #{pendingDecision.id} is already pending hiring manager approval.</Alert> : null}
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }} justifyContent="space-between">
        <Box>
          <Typography sx={{ fontWeight: 600 }}>Applicant comparison</Typography>
          <Typography variant="body2" color="text.secondary">Select 2 or 3 applicants in the Compare column.</Typography>
        </Box>
        <Button
          component={RouterLink}
          to={`/recruiter/jobs/${jobId}/applicant-comparison?applications=${comparisonSelected.join(',')}`}
          variant="outlined"
          disabled={comparisonSelected.length < 2}
        >
          Compare selected applicants ({comparisonSelected.length})
        </Button>
      </Stack>
      <Table><TableHead><TableRow><TableCell>Hire</TableCell><TableCell>Compare</TableCell><TableCell>Applicant</TableCell><TableCell>AI Match Score</TableCell><TableCell>Matched Skills</TableCell><TableCell>Missing Skills</TableCell><TableCell>AI Interview Summary</TableCell><TableCell>Interviewer remarks</TableCell><TableCell>Evidence</TableCell></TableRow></TableHead><TableBody>
        {data.applicants.map((applicant) => <TableRow key={applicant.application_id}>
          <TableCell><Checkbox checked={selected.includes(applicant.application_id)} disabled={noHire || !applicant.eligible_for_decision || (!selected.includes(applicant.application_id) && selected.length >= data.job.vacancies)} onChange={() => toggle(applicant.application_id)} /></TableCell>
          <TableCell><Checkbox inputProps={{ 'aria-label': `Compare ${applicant.applicant_name}` }} checked={comparisonSelected.includes(applicant.application_id)} disabled={!comparisonSelected.includes(applicant.application_id) && comparisonSelected.length >= 3} onChange={() => toggleComparison(applicant.application_id)} /></TableCell>
          <TableCell>{applicant.applicant_name}<Typography variant="caption" display="block">{applicant.applicant_email}{applicant.applicant_phone ? ` • ${applicant.applicant_phone}` : ''}</Typography>{applicant.resume_url ? <Button size="small" component="a" href={applicant.resume_url} target="_blank" rel="noreferrer">View resume</Button> : <Typography variant="caption" display="block">No resume</Typography>}</TableCell>
          <TableCell>{scoreText(applicant.ai_resume_score)}</TableCell>
          <TableCell>{(applicant.matched_skills || []).join(', ') || '—'}</TableCell>
          <TableCell>{(applicant.missing_skills || []).join(', ') || '—'}</TableCell>
          <TableCell>{(applicant.ai_interview_summaries || []).map((summary, index) => <Typography key={index} variant="body2">{summary}</Typography>)}{!applicant.ai_interview_summaries?.length ? '—' : null}</TableCell>
          <TableCell>{(applicant.interviewer_remarks || []).map((remark, index) => <Typography key={index} variant="body2">{remark}</Typography>)}{!applicant.interviewer_remarks?.length ? '—' : null}</TableCell>
          <TableCell><Stack alignItems="flex-start">{applicant.resume_url ? <Button size="small" component="a" href={applicant.resume_url} target="_blank" rel="noreferrer">View resume</Button> : null}{(applicant.interviews || []).map((interview) => <Button key={interview.id} size="small" component={RouterLink} to={`/recruiter/interviews/${interview.id}/evaluations?job_id=${jobId}`}>View interview evaluation</Button>)}</Stack></TableCell>
        </TableRow>)}
      </TableBody></Table>
      <Typography>{selected.length} of {data.job.vacancies} vacancy slots selected.</Typography>
      <FormControlLabel control={<Checkbox checked={noHire} onChange={(event) => { setNoHire(event.target.checked); if (event.target.checked) setSelected([]); }} />} label="Recommend No Hire (select no applicants)" />
      <TextField required multiline minRows={4} label="Recruiter justification" value={justification} onChange={(event) => setJustification(event.target.value)} />
      <Button variant="contained" disabled={Boolean(pendingDecision) || !data.readiness.ready || !justification.trim() || (!noHire && selected.length === 0)} onClick={submit}>Submit for hiring manager approval</Button>

      <Box sx={{ pt: 2 }}>
        <Typography component="h2" variant="h6" sx={{ fontWeight: 700 }}>Submitted hiring decisions</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Track every submission for this job, its hiring manager outcome, and the next action to take.
        </Typography>
        <TableContainer sx={{ border: 1, borderColor: 'divider', borderRadius: 1 }}>
          <Table size="small">
            <TableHead><TableRow><TableCell>Decision</TableCell><TableCell>Selected applicants</TableCell><TableCell>Status</TableCell><TableCell>Submitted</TableCell><TableCell>Hiring manager feedback</TableCell><TableCell>Next step</TableCell></TableRow></TableHead>
            <TableBody>
              {decisions.map((decision) => <TableRow key={decision.id}>
                <TableCell><Typography variant="body2" sx={{ fontWeight: 600 }}>#{decision.id} · {titleize(decision.decision_type)}</Typography></TableCell>
                <TableCell>{decision.items.length ? decision.items.map((item) => applicationName(item.application)).join(', ') : 'No applicants selected'}</TableCell>
                <TableCell><Chip size="small" color={decision.status === 'approved' ? 'success' : decision.status === 'rejected' ? 'error' : 'warning'} label={titleize(decision.status)} /></TableCell>
                <TableCell>{formatDateTime(decision.submitted_at)}</TableCell>
                <TableCell>{decision.hr_remarks || 'Awaiting feedback'}</TableCell>
                <TableCell>
                  <Typography variant="body2">{nextStep(decision)}</Typography>
                  {decision.status === 'approved' && decision.decision_type === 'recommend_hire' ? <Button component={RouterLink} to="/recruiter/job-offers" size="small" sx={{ mt: 0.5 }}>Go to job offers</Button> : null}
                </TableCell>
              </TableRow>)}
              {!decisions.length ? <TableRow><TableCell colSpan={6}>No hiring decisions have been submitted for this job yet.</TableCell></TableRow> : null}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </>}
  </Stack></Paper></Box>;
}
