import { useEffect, useState } from 'react';
import { Box, Button, Checkbox, Chip, CircularProgress, FormControlLabel, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useParams } from 'react-router-dom';
import { getJobApplicantComparison, getJobHiringDecisions, submitJobHiringDecision } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage, scoreText, titleize } from './recruiterUtils.js';

export default function HiringDecisionPage() {
  const { jobId } = useParams();
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState([]);
  const [noHire, setNoHire] = useState(false);
  const [justification, setJustification] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [pendingDecision, setPendingDecision] = useState(null);
  useEffect(() => {
    if (!jobId) return;
    Promise.all([getJobApplicantComparison(jobId), getJobHiringDecisions({ status: 'pending_hr_approval' })])
      .then(([comparison, decisions]) => {
        setData(comparison);
        setPendingDecision(decisions.find((decision) => decision.job_posting === Number(jobId)) || null);
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load applicant comparison.')));
  }, [jobId]);
  const toggle = (id) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  const submit = async () => {
    setError('');
    try {
      const result = await submitJobHiringDecision({ job_posting: Number(jobId), decision_type: noHire ? 'recommend_no_hire' : 'recommend_hire', application_ids: noHire ? [] : selected, justification });
      setPendingDecision(result);
      setSuccess(`Hiring Decision #${result.id} submitted. Status: Pending HR Approval.`);
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to submit hiring decision.')); }
  };
  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}><Stack spacing={2}>
    <Typography variant="h5" sx={{ fontWeight: 700 }}>Job-level Hiring Decision</Typography>
    <Typography color="text.secondary">Compare every applicant for this job. AI and interview evidence support, but do not replace, the human decision.</Typography>
    {error ? <Alert severity="error">{error}</Alert> : null}{success ? <Alert severity="success">{success}</Alert> : null}
    {!data ? <CircularProgress /> : <>
      <Typography><strong>{data.job.title}</strong> • {data.job.vacancies} vacancy/vacancies • {titleize(data.job.status)}</Typography>
      {pendingDecision ? <Alert severity="info">Hiring Decision #{pendingDecision.id} is already pending hiring manager approval.</Alert> : null}
      {!data.readiness.ready ? <Alert severity="warning">Not ready: {data.readiness.reasons.join(' ')}</Alert> : <Alert severity="success">Ready for Hiring Decision.</Alert>}
      <Table><TableHead><TableRow><TableCell>Select</TableCell><TableCell>Applicant</TableCell><TableCell>Application</TableCell><TableCell>AI score</TableCell><TableCell>Interview / evaluation</TableCell><TableCell>Evidence</TableCell></TableRow></TableHead><TableBody>
        {data.applicants.map((applicant) => <TableRow key={applicant.application_id}>
          <TableCell><Checkbox checked={selected.includes(applicant.application_id)} disabled={noHire || !applicant.eligible_for_decision || (!selected.includes(applicant.application_id) && selected.length >= data.job.vacancies)} onChange={() => toggle(applicant.application_id)} /></TableCell>
          <TableCell>{applicant.applicant_name}<Typography variant="caption" display="block">{applicant.recruiter_remark || 'No recruiter remarks'}</Typography></TableCell>
          <TableCell><Chip size="small" label={titleize(applicant.application_status)} /></TableCell><TableCell>{scoreText(applicant.ai_resume_score)}</TableCell>
          <TableCell>{applicant.interview_statuses.map(titleize).join(', ') || 'No interview'} / {titleize(applicant.evaluation_status)}<Typography variant="caption" display="block">Scorecards: {applicant.scorecards_submitted}/{applicant.scorecards_required} submitted</Typography><Typography variant="caption" display="block">{applicant.evaluation_score ?? 'No evaluation score'} {applicant.evaluation_summary}</Typography></TableCell>
          <TableCell>Transcript: {titleize(applicant.transcript_status)}<br />AI summary: {titleize(applicant.ai_summary_status)}<br />Skills: {(applicant.extracted_skills || []).join(', ') || '—'}</TableCell>
        </TableRow>)}
      </TableBody></Table>
      <Typography>{selected.length} of {data.job.vacancies} vacancy slots selected.</Typography>
      <FormControlLabel control={<Checkbox checked={noHire} onChange={(event) => { setNoHire(event.target.checked); if (event.target.checked) setSelected([]); }} />} label="Recommend No Hire (select no applicants)" />
      <TextField required multiline minRows={4} label="Recruiter justification" value={justification} onChange={(event) => setJustification(event.target.value)} />
      <Button variant="contained" disabled={Boolean(pendingDecision) || !data.readiness.ready || !justification.trim() || (!noHire && selected.length === 0)} onClick={submit}>Submit for hiring manager approval</Button>
    </>}
  </Stack></Paper></Box>;
}
