import { useEffect, useState } from 'react';
import { Box, Button, Checkbox, CircularProgress, FormControlLabel, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useParams } from 'react-router-dom';
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
      <Table><TableHead><TableRow><TableCell>Select</TableCell><TableCell>Applicant</TableCell><TableCell>AI Match Score</TableCell><TableCell>Matched Skills</TableCell><TableCell>Missing Skills</TableCell><TableCell>AI Interview Summary</TableCell><TableCell>Interviewer remarks</TableCell><TableCell>Evidence</TableCell></TableRow></TableHead><TableBody>
        {data.applicants.map((applicant) => <TableRow key={applicant.application_id}>
          <TableCell><Checkbox checked={selected.includes(applicant.application_id)} disabled={noHire || !applicant.eligible_for_decision || (!selected.includes(applicant.application_id) && selected.length >= data.job.vacancies)} onChange={() => toggle(applicant.application_id)} /></TableCell>
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
    </>}
  </Stack></Paper></Box>;
}
