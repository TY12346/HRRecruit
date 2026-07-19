import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
} from '@mui/material';
import { approveJobRequisition, getJobRequisitions, rejectJobRequisition } from '../../api/client.js';
import HiringManagerNav from './HiringManagerNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './hiringManagerUtils.js';

const departmentName = (item) => (item.department === 'Other' ? item.custom_department : item.department) || '—';

const DetailRow = ({ label, value }) => (
  <Box>
    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700, textTransform: 'uppercase' }}>{label}</Typography>
    <Typography sx={{ whiteSpace: 'pre-wrap' }}>{value || '—'}</Typography>
  </Box>
);

export default function JobRequisitionsPage() {
  const [requisitions, setRequisitions] = useState([]);
  const [selectedRequisition, setSelectedRequisition] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const load = () => getJobRequisitions()
    .then(setRequisitions)
    .catch((err) => setError(getApiErrorMessage(err, 'Unable to load job requisitions.')))
    .finally(() => setIsLoading(false));

  useEffect(() => { load(); }, []);

  const approve = async (item) => {
    setBusyId(item.id); setError(''); setSuccess('');
    try { await approveJobRequisition(item.id); setSuccess('Job requisition approved. A draft job was created for recruiter configuration.'); setSelectedRequisition(null); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to approve requisition.')); } finally { setBusyId(null); }
  };
  const reject = async (item) => {
    const reason = window.prompt('Reason for rejecting this job requisition');
    if (!reason) return;
    setBusyId(item.id); setError(''); setSuccess('');
    try { await rejectJobRequisition(item.id, reason); setSuccess('Job requisition rejected.'); setSelectedRequisition(null); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to reject requisition.')); } finally { setBusyId(null); }
  };

  return (
    <Box>
      <HiringManagerNav />
      <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 2 }}>Job Requisitions</Typography>
      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
      {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
      {isLoading ? <CircularProgress /> : null}
      <Stack spacing={0} sx={{ mt: 2 }}>
        {requisitions.map((item) => (
          <Stack key={item.id} direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1} sx={{ py: 1, borderTop: '1px solid', borderColor: 'divider', '&:first-of-type': { borderTop: 0 } }}>
            <Box>
              <Typography sx={{ fontWeight: 700 }}>{item.title}</Typography>
              <Typography color="text.secondary" variant="body2">
                {item.recruiter_name} • {departmentName(item)} • {item.location} • {titleize(item.employment_type)} • {item.salary_range || 'Salary range not specified'}
              </Typography>
              <Typography color="text.secondary" variant="body2">
                {titleize(item.position_status)} • Target start {item.target_start_date || 'not specified'} • Submitted {formatDateTime(item.created_at)}
              </Typography>
              <Typography color="text.secondary" variant="body2">Reason for hire: {item.reason_for_hire || '—'}</Typography>
              <Typography color="text.secondary" variant="body2">Impact of not hiring: {item.impact_of_not_hiring || '—'}</Typography>
              {item.status === 'rejected' ? <Typography color="error" variant="body2">Reason: {item.rejection_reason}</Typography> : null}
            </Box>
            <Stack direction="row" spacing={1} sx={{ ml: { md: 'auto' }, alignSelf: { xs: 'flex-start', md: 'center' } }}>
              <Chip label={titleize(item.status)} size="small" color={item.status === 'approved' ? 'success' : item.status === 'rejected' ? 'error' : 'warning'} />
              <Button onClick={() => setSelectedRequisition(item)} size="small" variant="outlined">View details</Button>
              {item.status === 'pending' ? <Button disabled={busyId === item.id} onClick={() => approve(item)} size="small" variant="contained">Approve</Button> : null}
              {item.status === 'pending' ? <Button disabled={busyId === item.id} onClick={() => reject(item)} size="small" color="error" variant="outlined">Reject</Button> : null}
            </Stack>
          </Stack>
        ))}
        {!isLoading && requisitions.length === 0 ? <Typography color="text.secondary">No job requisitions yet.</Typography> : null}
      </Stack>

      <Dialog open={Boolean(selectedRequisition)} onClose={() => setSelectedRequisition(null)} fullWidth maxWidth="md">
        {selectedRequisition ? (
          <>
            <DialogTitle>{selectedRequisition.title}</DialogTitle>
            <DialogContent dividers>
              <Stack spacing={2}>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                  <DetailRow label="Status" value={titleize(selectedRequisition.status)} />
                  <DetailRow label="Recruiter" value={selectedRequisition.recruiter_name} />
                  <DetailRow label="Submitted" value={formatDateTime(selectedRequisition.created_at)} />
                </Stack>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                  <DetailRow label="Department" value={departmentName(selectedRequisition)} />
                  <DetailRow label="Position status" value={titleize(selectedRequisition.position_status)} />
                  <DetailRow label="Target start date" value={selectedRequisition.target_start_date} />
                </Stack>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                  <DetailRow label="Employment type" value={titleize(selectedRequisition.employment_type)} />
                  <DetailRow label="Location" value={selectedRequisition.location} />
                  <DetailRow label="Salary range" value={selectedRequisition.salary_range} />
                </Stack>
                <DetailRow label="Job summary" value={selectedRequisition.description} />
                <DetailRow label="Core responsibilities" value={selectedRequisition.core_responsibilities} />
                <DetailRow label="Requirements & qualifications" value={selectedRequisition.requirements_qualifications} />
                <DetailRow label="Benefits & perks" value={selectedRequisition.benefits_perks} />
                <DetailRow label="Reason for hire" value={selectedRequisition.reason_for_hire} />
                <DetailRow label="Impact of not hiring" value={selectedRequisition.impact_of_not_hiring} />
                {selectedRequisition.status === 'rejected' ? <DetailRow label="Rejection reason" value={selectedRequisition.rejection_reason} /> : null}
                {selectedRequisition.status === 'approved' && selectedRequisition.job_posting_id ? <DetailRow label="Draft job" value={`Job #${selectedRequisition.job_posting_id}`} /> : null}
              </Stack>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedRequisition(null)}>Close</Button>
              {selectedRequisition.status === 'pending' ? <Button disabled={busyId === selectedRequisition.id} onClick={() => reject(selectedRequisition)} color="error" variant="outlined">Reject</Button> : null}
              {selectedRequisition.status === 'pending' ? <Button disabled={busyId === selectedRequisition.id} onClick={() => approve(selectedRequisition)} variant="contained">Approve</Button> : null}
            </DialogActions>
          </>
        ) : null}
      </Dialog>
    </Box>
  );
}
