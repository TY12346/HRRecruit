import { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { approveJobRequisition, getJobRequisitions, rejectJobRequisition } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './hrHeadUtils.js';

export default function JobRequisitionsPage() {
  const [requisitions, setRequisitions] = useState([]);
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
    try { await approveJobRequisition(item.id); setSuccess('Job requisition approved and posted.'); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to approve requisition.')); } finally { setBusyId(null); }
  };
  const reject = async (item) => {
    const reason = window.prompt('Reason for rejecting this job requisition');
    if (!reason) return;
    setBusyId(item.id); setError(''); setSuccess('');
    try { await rejectJobRequisition(item.id, reason); setSuccess('Job requisition rejected.'); await load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to reject requisition.')); } finally { setBusyId(null); }
  };

  return (
    <Box>
      <HRHeadNav />
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
                {item.recruiter_name} • {item.location} • {titleize(item.employment_type)} • Submitted {formatDateTime(item.created_at)}
              </Typography>
              {item.status === 'rejected' ? <Typography color="error" variant="body2">Reason: {item.rejection_reason}</Typography> : null}
            </Box>
            <Stack direction="row" spacing={1} sx={{ ml: { md: 'auto' } }}>
              <Chip label={titleize(item.status)} size="small" color={item.status === 'approved' ? 'success' : item.status === 'rejected' ? 'error' : 'warning'} />
              {item.status === 'pending' ? <Button disabled={busyId === item.id} onClick={() => approve(item)} size="small" variant="contained">Approve</Button> : null}
              {item.status === 'pending' ? <Button disabled={busyId === item.id} onClick={() => reject(item)} size="small" color="error" variant="outlined">Reject</Button> : null}
            </Stack>
          </Stack>
        ))}
        {!isLoading && requisitions.length === 0 ? <Typography color="text.secondary">No job requisitions yet.</Typography> : null}
      </Stack>
    </Box>
  );
}
