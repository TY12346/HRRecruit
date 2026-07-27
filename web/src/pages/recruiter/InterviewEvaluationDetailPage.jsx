import { useCallback, useEffect, useMemo, useState } from 'react';
import { Box, Button, Card, CardContent, Chip, CircularProgress, Grid, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { getInterviews, getJobs } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

const statuses = ['invited', 'scheduled', 'cancelled', 'completed', 'evaluation_submitted'];
const modes = ['online', 'physical', 'phone'];
const fields = ['search', 'job_id', 'status', 'mode', 'date_from', 'date_to', 'attention'];
const attentionFor = (interview) => {
  const deliverable = interview.deliverable_status || {};
  const transcript = interview.transcript?.processing_status;
  if (interview.status === 'invited') return interview.availability_alert ? 'No common panel availability' : 'Waiting for applicant scheduling';
  if (transcript === 'processing') return 'Transcript processing';
  if (transcript === 'failed') return 'Transcript failed';
  if (transcript === 'low_quality') return 'Transcript low quality';
  if (deliverable.is_late) return 'Deliverables late';
  if (deliverable.is_almost_late) return 'Deliverables almost late';
  if ((deliverable.submitted_evaluation_count ?? 0) < (deliverable.required_evaluation_count ?? 0)) return 'Evaluation incomplete';
  return '';
};

export default function InterviewEvaluationDetailPage() {
  const [params, setParams] = useSearchParams();
  const filters = Object.fromEntries(fields.map((key) => [key, params.get(key) || '']));
  const [interviews, setInterviews] = useState([]); const [jobs, setJobs] = useState([]);
  const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { const [records, ownedJobs] = await Promise.all([getInterviews(Object.fromEntries(Object.entries(filters).filter(([key, value]) => value && key !== 'attention'))), getJobs()]); setInterviews(records); setJobs(ownedJobs); }
    catch (err) { setError(getApiErrorMessage(err, 'Unable to load interviews.')); } finally { setLoading(false); }
  // URL parameters are the source of truth.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.toString()]);
  useEffect(() => { load(); }, [load]);
  const shown = useMemo(() => filters.attention ? interviews.filter((item) => attentionFor(item) === filters.attention) : interviews, [filters.attention, interviews]);
  const selectedJob = jobs.find((job) => String(job.id) === filters.job_id);
  const update = (key, value) => { const next = new URLSearchParams(params); value ? next.set(key, value) : next.delete(key); setParams(next); };
  const summary = {
    'Upcoming interviews': interviews.filter((i) => i.status === 'scheduled' && new Date(i.scheduled_datetime) >= new Date()).length,
    'Awaiting applicant scheduling': interviews.filter((i) => i.status === 'invited').length,
    'Completed interviews': interviews.filter((i) => ['completed', 'evaluation_submitted'].includes(i.status)).length,
    'Pending panel evaluations': interviews.filter((i) => (i.deliverable_status?.submitted_evaluation_count ?? 0) < (i.deliverable_status?.required_evaluation_count ?? 0)).length,
    'Interviews requiring attention': interviews.filter(attentionFor).length,
  };
  return <Box><RecruiterNav /><Paper sx={{ p: { xs: 2, md: 3 } }}>
    <Stack spacing={1} sx={{ mb: 3 }}><Typography component="h1" variant="h5" fontWeight={700}>{selectedJob ? `Interviews for ${selectedJob.title}` : 'Interviews across all jobs'}</Typography>
      <Typography color="text.secondary">{selectedJob ? `Showing records for ${selectedJob.title}.` : 'View and monitor interviews across all jobs you manage.'}</Typography>
      {selectedJob ? <Stack direction="row" spacing={1}><Button component={RouterLink} to={`/recruiter/jobs/${selectedJob.id}`}>Back to job</Button><Button onClick={() => update('job_id', '')}>View interviews for all jobs</Button></Stack> : null}</Stack>
    {error ? <Alert severity="error" action={<Button color="inherit" onClick={load}>Retry</Button>}>{error}</Alert> : null}
    <Grid container spacing={2} sx={{ mb: 3 }}>{Object.entries(summary).map(([label, value]) => <Grid item xs={12} sm={6} md key={label}><Card variant="outlined"><CardContent><Typography color="text.secondary" variant="body2">{label}</Typography><Typography variant="h4">{value}</Typography></CardContent></Card></Grid>)}</Grid>
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} useFlexGap flexWrap="wrap">
      <TextField size="small" label="Search" value={filters.search} onChange={(e) => update('search', e.target.value)} />
      <TextField select size="small" label="Job" value={filters.job_id} onChange={(e) => update('job_id', e.target.value)} sx={{ minWidth: 180 }}><MenuItem value="">All jobs</MenuItem>{jobs.map((j) => <MenuItem key={j.id} value={j.id}>{j.title}</MenuItem>)}</TextField>
      <TextField select size="small" label="Status" value={filters.status} onChange={(e) => update('status', e.target.value)} sx={{ minWidth: 150 }}><MenuItem value="">All statuses</MenuItem>{statuses.map((v) => <MenuItem key={v} value={v}>{titleize(v)}</MenuItem>)}</TextField>
      <TextField select size="small" label="Mode" value={filters.mode} onChange={(e) => update('mode', e.target.value)} sx={{ minWidth: 130 }}><MenuItem value="">All modes</MenuItem>{modes.map((v) => <MenuItem key={v} value={v}>{titleize(v)}</MenuItem>)}</TextField>
      {['date_from', 'date_to'].map((key) => <TextField key={key} size="small" type="date" label={key === 'date_from' ? 'Date from' : 'Date to'} InputLabelProps={{ shrink: true }} value={filters[key]} onChange={(e) => update(key, e.target.value)} />)}
      <TextField select size="small" label="Attention" value={filters.attention} onChange={(e) => update('attention', e.target.value)} sx={{ minWidth: 190 }}><MenuItem value="">All</MenuItem>{['Waiting for applicant scheduling', 'No common panel availability', 'Evaluation incomplete', 'Deliverables almost late', 'Deliverables late', 'Transcript processing', 'Transcript failed', 'Transcript low quality'].map((v) => <MenuItem key={v} value={v}>{v}</MenuItem>)}</TextField>
      {params.toString() ? <Button onClick={() => setParams({})}>Reset filters</Button> : null}
    </Stack>
    {loading ? <CircularProgress aria-label="Loading interviews" sx={{ mt: 3 }} /> : <Box sx={{ overflowX: 'auto' }}><Table sx={{ mt: 2, minWidth: 1250 }}><TableHead><TableRow>{['Applicant', 'Job', 'Primary interviewer', 'Panel members', 'Scheduled', 'Mode / venue', 'Status', 'Evaluation progress', 'Deliverables', 'Actions'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead><TableBody>
      {shown.map((i) => { const d = i.deliverable_status || {}; const attention = attentionFor(i); return <TableRow key={i.id}><TableCell>{i.application?.applicant?.full_name || '—'}</TableCell><TableCell>{i.application?.job_title || '—'}</TableCell><TableCell>{i.interviewer?.full_name || '—'}</TableCell><TableCell>{(i.panel_interviewers || []).map((p) => p.full_name).join(', ') || '—'}</TableCell><TableCell>{formatDateTime(i.scheduled_datetime)}</TableCell><TableCell>{titleize(i.mode)}<Typography variant="body2">{i.meeting_link || i.location || '—'}</Typography></TableCell><TableCell><Chip size="small" label={titleize(i.status)} /></TableCell><TableCell>{d.submitted_evaluation_count ?? 0} of {d.required_evaluation_count ?? 0} evaluations submitted</TableCell><TableCell>{attention ? <Chip size="small" color="warning" label={attention} /> : <Chip size="small" color="success" label={d.is_complete ? 'Complete' : 'On track'} />}</TableCell><TableCell><Stack><Button component={RouterLink} to={`/recruiter/applications/${i.application?.id}`}>View applicant</Button><Button component={RouterLink} to={`/recruiter/jobs/${i.application?.job}`}>View job</Button>{(d.required_evaluation_count ?? 0) > 0 ? <Button component={RouterLink} to={`/recruiter/interviews/${i.id}/evaluations`}>View evaluations</Button> : null}</Stack></TableCell></TableRow>; })}
      {!shown.length ? <TableRow><TableCell colSpan={10}>No interviews match the current filters.</TableCell></TableRow> : null}
    </TableBody></Table></Box>}
  </Paper></Box>;
}
