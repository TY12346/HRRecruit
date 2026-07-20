import { useEffect, useMemo, useState } from 'react';
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
  const [search, setSearch] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
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

  const visibleRequisitions = useMemo(() => {
    const searchTerm = submittedSearch.trim().toLowerCase();
    if (!searchTerm) {
      return requisitions;
    }

    return requisitions.filter((item) => [
      item.title,
      item.recruiter_name,
      departmentName(item),
      item.location,
      item.employment_type,
      item.position_status,
      item.status,
    ].some((value) => String(value ?? '').toLowerCase().includes(searchTerm)));
  }, [requisitions, submittedSearch]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setSubmittedSearch(search);
  };

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
      <Paper sx={{ p: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
            Job Requisitions
          </Typography>
          <Typography color="text.secondary">
            Review submitted job requisitions and approve or reject them when required.
          </Typography>
        </Box>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}

        <Box component="form" onSubmit={handleSearchSubmit} sx={{ mb: 2 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <TextField
              fullWidth
              label="Search by title, recruiter, department, or status"
              onChange={(event) => setSearch(event.target.value)}
              value={search}
            />
            <Button type="submit" variant="outlined">Search</Button>
          </Stack>
        </Box>

        {isLoading ? <CircularProgress aria-label="Loading job requisitions" /> : null}

        <Table sx={{ mt: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Recruiter</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Position status</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Submitted</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleRequisitions.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.title}</TableCell>
                <TableCell>{item.recruiter_name || '—'}</TableCell>
                <TableCell>{departmentName(item)}</TableCell>
                <TableCell>{titleize(item.position_status)}</TableCell>
                <TableCell>
                  <Chip label={titleize(item.status)} size="small" color={item.status === 'approved' ? 'success' : item.status === 'rejected' ? 'error' : 'warning'} />
                </TableCell>
                <TableCell>{formatDateTime(item.created_at)}</TableCell>
                <TableCell align="right">
                  <Stack direction="row" justifyContent="flex-end" spacing={1}>
                    <Button onClick={() => setSelectedRequisition(item)} size="small" variant="outlined">View details</Button>
                    {item.status === 'pending' ? <Button disabled={busyId === item.id} onClick={() => approve(item)} size="small" variant="contained">Approve</Button> : null}
                    {item.status === 'pending' ? <Button disabled={busyId === item.id} onClick={() => reject(item)} size="small" color="error" variant="outlined">Reject</Button> : null}
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && visibleRequisitions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7}>{submittedSearch ? 'No job requisitions match your search.' : 'No job requisitions found.'}</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>

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
