import { useCallback, useEffect, useState } from 'react';
import { Box, Button, Card, CardContent, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { approveJobHiringDecision, getJobHiringDecisions, rejectJobHiringDecision } from '../../api/client.js';
import HiringManagerNav from './HiringManagerNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './hiringManagerUtils.js';

export default function PendingHiringDecisionsPage() {
  const [decisions, setDecisions] = useState([]);
  const [review, setReview] = useState(null);
  const [remarks, setRemarks] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => { setLoading(true); try { setDecisions(await getJobHiringDecisions({ status: 'pending_hr_approval' })); } catch (err) { setError(getApiErrorMessage(err, 'Unable to load hiring decisions.')); } finally { setLoading(false); } }, []);
  useEffect(() => { load(); }, [load]);
  const submit = async () => { try { if (review.action === 'approve') await approveJobHiringDecision(review.item.id, remarks); else await rejectJobHiringDecision(review.item.id, remarks); setSuccess(`Hiring decision ${review.action === 'approve' ? 'approved' : 'returned for review'}.`); setReview(null); setRemarks(''); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to review decision.')); } };
  return <Box><HiringManagerNav /><Stack spacing={3}>
    <Box><Typography variant="h5" sx={{ fontWeight: 700 }}>Pending Job-level Hiring Decisions</Typography><Typography color="text.secondary">Approve or reject the decision for the job posting as a whole.</Typography></Box>
    {error ? <Alert severity="error">{error}</Alert> : null}{success ? <Alert severity="success">{success}</Alert> : null}{loading ? <CircularProgress /> : null}
    {!loading && decisions.length === 0 ? <Alert severity="info">No job-level decisions are pending hiring manager approval.</Alert> : null}
    {decisions.map((item) => <Card key={item.id}><CardContent><Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between"><Box><Typography variant="h6">{item.job_title}</Typography><Typography color="text.secondary">{titleize(item.decision_type)} • {item.vacancies} vacancy/vacancies • {item.organization_name}</Typography><Typography variant="caption">Submitted by {item.recruiter_name} on {formatDateTime(item.submitted_at)}</Typography></Box><Stack direction="row" spacing={1}><Button color="success" variant="contained" onClick={() => setReview({ item, action: 'approve' })}>Approve</Button><Button color="error" variant="outlined" onClick={() => setReview({ item, action: 'reject' })}>Reject</Button></Stack></Stack>
      <Typography><strong>Recruiter justification:</strong> {item.justification}</Typography>
      <Typography><strong>Selected applicants:</strong> {item.items.length ? item.items.map((applicant) => applicant.application?.applicant?.full_name).join(', ') : 'None — Recommend No Hire'}</Typography>
      <Typography><strong>Full applicant comparison:</strong></Typography>
      {(item.applicant_pool || []).map((applicant) => <Box key={applicant.id} sx={{ pl: 2 }}><Typography variant="body2">{applicant.applicant?.full_name} • {titleize(applicant.status)} • AI resume score {applicant.final_score ?? '—'} • Skills {(applicant.extracted_skills || []).join(', ') || '—'}</Typography></Box>)}
      {item.items.map((applicant) => <Box key={applicant.id} sx={{ borderLeft: 3, borderColor: 'primary.main', pl: 2 }}><Typography>{applicant.selection_order}. {applicant.application?.applicant?.full_name} <Chip size="small" label={titleize(applicant.application?.status)} /></Typography><Typography variant="body2">AI resume score: {applicant.application?.final_score ?? '—'} • Evaluation evidence completed before submission</Typography></Box>)}
    </Stack></CardContent></Card>)}
  </Stack><Dialog open={Boolean(review)} onClose={() => setReview(null)} fullWidth><DialogTitle>{review?.action === 'approve' ? 'Approve' : 'Reject / return'} job-level decision</DialogTitle><DialogContent><TextField autoFocus fullWidth multiline minRows={4} sx={{ mt: 1 }} label="HR remarks (optional)" value={remarks} onChange={(event) => setRemarks(event.target.value)} /></DialogContent><DialogActions><Button onClick={() => setReview(null)}>Cancel</Button><Button variant="contained" onClick={submit}>{review?.action === 'approve' ? 'Approve' : 'Reject'}</Button></DialogActions></Dialog></Box>;
}
