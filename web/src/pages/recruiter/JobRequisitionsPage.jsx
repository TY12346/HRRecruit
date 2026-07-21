import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
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
import { Link as RouterLink } from 'react-router-dom';
import { getJobRequisitions } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

const departmentName = (item) => (item.department === 'Other' ? item.custom_department : item.department) || '—';

export default function JobRequisitionsPage() {
  const [requisitions, setRequisitions] = useState([]);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getJobRequisitions()
      .then(setRequisitions)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load job requisitions.')))
      .finally(() => setIsLoading(false));
  }, []);

  const visibleRequisitions = useMemo(() => {
    const searchTerm = search.trim().toLowerCase();
    if (!searchTerm) {
      return requisitions;
    }

    return requisitions.filter((item) => [
      item.title,
      departmentName(item),
      item.location,
      item.employment_type,
      item.position_status,
      item.status,
    ].some((value) => String(value ?? '').toLowerCase().includes(searchTerm)));
  }, [requisitions, search]);

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 3 }}>
          <Box>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
              Job Requisitions
            </Typography>
          </Box>
          <Button component={RouterLink} to="/recruiter/jobs/create" variant="contained">
            Create requisition
          </Button>
        </Stack>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}

        <TextField
          fullWidth
          label="Search by title, department, location, or status"
          onChange={(event) => setSearch(event.target.value)}
          sx={{ mb: 2 }}
          value={search}
        />

        {isLoading ? <CircularProgress aria-label="Loading job requisitions" /> : null}

        <Table sx={{ mt: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Employment type</TableCell>
              <TableCell>Position status</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Submitted</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleRequisitions.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <Typography sx={{ fontWeight: 700 }}>{item.title}</Typography>
                  {item.status === 'rejected' ? <Typography color="error" variant="body2">Reason: {item.rejection_reason}</Typography> : null}
                  {item.status === 'approved' && item.job_posting_id ? <Typography color="text.secondary" variant="body2">Draft job #{item.job_posting_id}</Typography> : null}
                </TableCell>
                <TableCell>{departmentName(item)}</TableCell>
                <TableCell>{item.location || '—'}</TableCell>
                <TableCell>{titleize(item.employment_type)}</TableCell>
                <TableCell>{titleize(item.position_status)}</TableCell>
                <TableCell>
                  <Chip label={titleize(item.status)} size="small" color={item.status === 'approved' ? 'success' : item.status === 'rejected' ? 'error' : 'warning'} />
                </TableCell>
                <TableCell>{formatDateTime(item.created_at)}</TableCell>
              </TableRow>
            ))}
            {!isLoading && visibleRequisitions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7}>{search ? 'No job requisitions match your search.' : 'No job requisitions yet.'}</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
