import { useEffect, useState } from 'react';
import { Alert, Box, Button, Checkbox, Chip, CircularProgress, FormControlLabel, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useParams } from 'react-router-dom';
import { getJobCandidateComparison, submitJobHiringRecommendation } from '../../api/client.js';
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
  useEffect(() => { if (jobId) getJobCandidateComparison(jobId).then(setData).catch((err) => setError(getApiErrorMessage(err, 'Unable to load candidate comparison.'))); }, [jobId]);
  const toggle = (id) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  const submit = async () => {
    setError('');
    try {
      const result = await submitJobHiringRecommendation({ job_posting: Number(jobId), recommendation_type: noHire ? 'recommend_no_hire' : 'recommend_hire', application_ids: noHire ? [] : selected, justification });
      setSuccess(`Hiring Recommendation #${result.id} submitted. Status: Pending HR Approval.`);
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to submit hiring recommendation.')); }
  };
  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}><Stack spacing={2}>
    <Typography variant="h5" sx={{ fontWeight: 700 }}>Job-level Hiring Recommendation</Typography>
    <Typography color="text.secondary">Compare every candidate for this job. AI and interview evidence support, but do not replace, the human decision.</Typography>
    {error ? <Alert severity="error">{error}</Alert> : null}{success ? <Alert severity="success">{success}</Alert> : null}
    {!data ? <CircularProgress /> : <>
      <Typography><strong>{data.job.title}</strong> • {data.job.vacancies} vacancy/vacancies • {titleize(data.job.status)}</Typography>
      {!data.readiness.ready ? <Alert severity="warning">Not ready: {data.readiness.reasons.join(' ')}</Alert> : <Alert severity="success">Ready for Hiring Recommendation.</Alert>}
      <Table><TableHead><TableRow><TableCell>Select</TableCell><TableCell>Candidate</TableCell><TableCell>Application</TableCell><TableCell>AI score</TableCell><TableCell>Interview / evaluation</TableCell><TableCell>Evidence</TableCell></TableRow></TableHead><TableBody>
        {data.candidates.map((candidate) => <TableRow key={candidate.application_id}>
          <TableCell><Checkbox checked={selected.includes(candidate.application_id)} disabled={noHire || !candidate.eligible_for_recommendation || (!selected.includes(candidate.application_id) && selected.length >= data.job.vacancies)} onChange={() => toggle(candidate.application_id)} /></TableCell>
          <TableCell>{candidate.candidate_name}<Typography variant="caption" display="block">{candidate.recruiter_remark || 'No recruiter remarks'}</Typography></TableCell>
          <TableCell><Chip size="small" label={titleize(candidate.application_status)} /></TableCell><TableCell>{scoreText(candidate.ai_resume_score)}</TableCell>
          <TableCell>{candidate.interview_statuses.map(titleize).join(', ') || 'No interview'} / {titleize(candidate.evaluation_status)}<Typography variant="caption" display="block">{candidate.evaluation_score ?? 'No evaluation score'} {candidate.evaluation_summary}</Typography></TableCell>
          <TableCell>Transcript: {titleize(candidate.transcript_status)}<br />AI summary: {titleize(candidate.ai_summary_status)}<br />Skills: {(candidate.extracted_skills || []).join(', ') || '—'}</TableCell>
        </TableRow>)}
      </TableBody></Table>
      <Typography>{selected.length} of {data.job.vacancies} vacancy slots selected.</Typography>
      <FormControlLabel control={<Checkbox checked={noHire} onChange={(event) => { setNoHire(event.target.checked); if (event.target.checked) setSelected([]); }} />} label="Recommend No Hire (select no candidates)" />
      <TextField required multiline minRows={4} label="Recruiter justification" value={justification} onChange={(event) => setJustification(event.target.value)} />
      <Button variant="contained" disabled={!data.readiness.ready || !justification.trim() || (!noHire && selected.length === 0)} onClick={submit}>Submit for HR approval</Button>
    </>}
  </Stack></Paper></Box>;
}
