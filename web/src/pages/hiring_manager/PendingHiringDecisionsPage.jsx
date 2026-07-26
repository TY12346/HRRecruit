import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { approveJobHiringDecision, getJobHiringDecisions, rejectJobHiringDecision } from '../../api/client.js';
import HiringManagerNav from './HiringManagerNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './hiringManagerUtils.js';

const selectedApplicantsFor = (decision) => decision.items
  ?.map((item) => item.application?.applicant?.full_name)
  .filter(Boolean)
  .join(', ') || 'None — Recommend No Hire';

export default function PendingHiringDecisionsPage() {
  const [decisions, setDecisions] = useState([]);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [remarks, setRemarks] = useState('');
  const [search, setSearch] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setDecisions(await getJobHiringDecisions({ status: 'pending_hr_approval' }));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load hiring decisions.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const visibleDecisions = useMemo(() => {
    const term = submittedSearch.trim().toLowerCase();
    if (!term) return decisions;

    return decisions.filter((decision) => [
      decision.job_title,
      decision.decision_type,
      decision.organization_name,
      decision.recruiter_name,
      selectedApplicantsFor(decision),
    ].some((value) => String(value ?? '').toLowerCase().includes(term)));
  }, [decisions, submittedSearch]);

  const closeDetails = () => {
    if (submitting) return;
    setSelectedDecision(null);
    setRemarks('');
  };

  const submit = async (action) => {
    setSubmitting(true);
    setError('');
    try {
      if (action === 'approve') {
        await approveJobHiringDecision(selectedDecision.id, remarks);
      } else {
        await rejectJobHiringDecision(selectedDecision.id, remarks);
      }
      setSuccess(`Hiring decision ${action === 'approve' ? 'approved' : 'returned for review'}.`);
      setSelectedDecision(null);
      setRemarks('');
      await load();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to review decision.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <HiringManagerNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h1" variant="h5" sx={{ mb: 3, fontWeight: 700 }}>
          Pending Job-level Hiring Decisions
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}

        <Box
          component="form"
          onSubmit={(event) => { event.preventDefault(); setSubmittedSearch(search); }}
          sx={{ mb: 2 }}
        >
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <TextField
              fullWidth
              label="Search by job, decision, recruiter, organization, or applicant"
              onChange={(event) => setSearch(event.target.value)}
              value={search}
            />
            <Button type="submit" variant="outlined">Search</Button>
          </Stack>
        </Box>

        {loading ? <CircularProgress aria-label="Loading hiring decisions" /> : null}

        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Job Title</TableCell>
              <TableCell>Decision</TableCell>
              <TableCell>Vacancies</TableCell>
              <TableCell>Submitted By</TableCell>
              <TableCell>Submitted</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleDecisions.map((decision) => (
              <TableRow key={decision.id}>
                <TableCell>{decision.job_title}</TableCell>
                <TableCell><Chip label={titleize(decision.decision_type)} size="small" /></TableCell>
                <TableCell>{decision.vacancies}</TableCell>
                <TableCell>{decision.recruiter_name}</TableCell>
                <TableCell>{formatDateTime(decision.submitted_at)}</TableCell>
                <TableCell align="center">
                  <Button size="small" onClick={() => setSelectedDecision(decision)}>View</Button>
                </TableCell>
              </TableRow>
            ))}
            {!loading && visibleDecisions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6}>
                  {submittedSearch
                    ? 'No pending hiring decisions match your search.'
                    : 'No job-level decisions are pending hiring manager approval.'}
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={Boolean(selectedDecision)} onClose={closeDetails} fullWidth maxWidth="md">
        <DialogTitle>Job-level Hiring Decision</DialogTitle>
        <DialogContent dividers>
          {selectedDecision ? (
            <Stack spacing={2}>
              <Box>
                <Typography variant="h6">{selectedDecision.job_title}</Typography>
                <Typography color="text.secondary">
                  {titleize(selectedDecision.decision_type)} • {selectedDecision.vacancies} vacancy/vacancies • {selectedDecision.organization_name}
                </Typography>
                <Typography variant="caption">
                  Submitted by {selectedDecision.recruiter_name} on {formatDateTime(selectedDecision.submitted_at)}
                </Typography>
              </Box>
              <Typography><strong>Recruiter justification:</strong> {selectedDecision.justification}</Typography>
              <Typography><strong>Selected applicants:</strong> {selectedApplicantsFor(selectedDecision)}</Typography>
              <Box>
                <Typography sx={{ mb: 1 }}><strong>Full applicant comparison:</strong></Typography>
                {(selectedDecision.applicant_pool || []).map((applicant) => (
                  <Typography key={applicant.id} variant="body2" sx={{ mb: 0.75, pl: 2 }}>
                    {applicant.applicant?.full_name} • {titleize(applicant.status)} • AI resume score {applicant.final_score ?? '—'} • Skills {(applicant.extracted_skills || []).join(', ') || '—'}
                  </Typography>
                ))}
              </Box>
              <TextField
                fullWidth
                multiline
                minRows={3}
                label="Hiring manager remarks (optional)"
                value={remarks}
                onChange={(event) => setRemarks(event.target.value)}
              />
            </Stack>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDetails} disabled={submitting}>Cancel</Button>
          <Button color="error" variant="outlined" onClick={() => submit('reject')} disabled={submitting}>Reject</Button>
          <Button color="success" variant="contained" onClick={() => submit('approve')} disabled={submitting}>Approve</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
