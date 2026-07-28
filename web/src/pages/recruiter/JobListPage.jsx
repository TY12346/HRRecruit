import { useEffect, useMemo, useState } from 'react';
import {
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
import Alert from '../../components/TimedAlert.jsx';
import { deleteJob, getJobs } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

const salaryFor = (job) => job.salary_range?.trim() || job.approximate_salary || 'Not specified';

export default function JobListPage() {
  const [jobs, setJobs] = useState([]);
  const [search, setSearch] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const loadJobs = async () => {
    setIsLoading(true);
    setError('');
    try {
      setJobs(await getJobs());
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load jobs.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const visibleJobs = useMemo(() => {
    const searchTerm = submittedSearch.trim().toLowerCase();
    if (!searchTerm) {
      return jobs;
    }

    return jobs.filter((job) => [
      job.title,
      job.status,
      job.employment_type,
      job.location,
      salaryFor(job),
    ].some((value) => String(value ?? '').toLowerCase().includes(searchTerm)));
  }, [jobs, submittedSearch]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setSubmittedSearch(search);
  };

  const handleDelete = async (job) => {
    if (!window.confirm(`Delete ${job.title}? This is only allowed if no applicant has reached a scheduled interview or beyond.`)) return;

    setError('');
    try {
      await deleteJob(job.id);
      setSuccess('Job deleted.');
      loadJobs();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to delete job.'));
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ mb: 3, fontWeight: 700 }}>
          Jobs
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}

        <Box component="form" onSubmit={handleSearchSubmit} sx={{ mb: 2 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <TextField
              fullWidth
              label="Search by title, status, type, location, or salary"
              onChange={(event) => setSearch(event.target.value)}
              value={search}
            />
            <Button type="submit" variant="outlined">Search</Button>
          </Stack>
        </Box>

        {isLoading ? <CircularProgress aria-label="Loading jobs" /> : null}

        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Salary</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleJobs.map((job) => (
              <TableRow key={job.id}>
                <TableCell>{job.title}</TableCell>
                <TableCell><Chip label={titleize(job.status)} size="small" color={job.status === 'open' ? 'success' : 'default'} /></TableCell>
                <TableCell>{job.employment_type}</TableCell>
                <TableCell>{job.location}</TableCell>
                <TableCell>{salaryFor(job)}</TableCell>
                <TableCell>{formatDateTime(job.created_at)}</TableCell>
                <TableCell align="center">
                  <Stack direction="row" spacing={1} justifyContent="center">
                    <Button component={RouterLink} to={`/recruiter/jobs/${job.id}`} size="small">View</Button>
                    <Button color="error" onClick={() => handleDelete(job)} size="small">Delete</Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && visibleJobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7}>{submittedSearch ? 'No jobs match your search.' : 'No jobs yet.'}</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
