import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableSortLabel,
  TextField,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import Alert from '../../components/TimedAlert.jsx';
import { deleteJob, getJobs } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

const salaryFor = (job) => job.salary_range?.trim() || job.approximate_salary || 'Not specified';

const salaryValue = (job) => {
  const match = String(salaryFor(job)).replace(/,/g, '').match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : Number.NEGATIVE_INFINITY;
};

const sortValues = {
  title: (job) => job.title ?? '',
  status: (job) => job.status ?? '',
  employment_type: (job) => job.employment_type ?? '',
  location: (job) => job.location ?? '',
  salary: salaryValue,
  created_at: (job) => new Date(job.created_at).getTime(),
};

export default function JobListPage() {
  const [jobs, setJobs] = useState([]);
  const [search, setSearch] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
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

  const filterOptions = useMemo(() => ({
    statuses: [...new Set(jobs.map((job) => job.status).filter(Boolean))].sort(),
    types: [...new Set(jobs.map((job) => job.employment_type).filter(Boolean))].sort(),
    locations: [...new Set(jobs.map((job) => job.location).filter(Boolean))].sort(),
  }), [jobs]);

  const visibleJobs = useMemo(() => {
    const searchTerm = submittedSearch.trim().toLowerCase();
    const filteredJobs = jobs.filter((job) => (
      (!searchTerm || [
        job.title,
        job.status,
        job.employment_type,
        job.location,
        salaryFor(job),
      ].some((value) => String(value ?? '').toLowerCase().includes(searchTerm)))
      && (!statusFilter || job.status === statusFilter)
      && (!typeFilter || job.employment_type === typeFilter)
      && (!locationFilter || job.location === locationFilter)
    ));

    const valueFor = sortValues[sortBy];
    return [...filteredJobs].sort((firstJob, secondJob) => {
      const firstValue = valueFor(firstJob);
      const secondValue = valueFor(secondJob);
      const comparison = typeof firstValue === 'string'
        ? firstValue.localeCompare(secondValue, undefined, { numeric: true, sensitivity: 'base' })
        : firstValue - secondValue;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [jobs, submittedSearch, statusFilter, typeFilter, locationFilter, sortBy, sortDirection]);

  const hasActiveFilters = Boolean(submittedSearch || statusFilter || typeFilter || locationFilter);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setSubmittedSearch(search);
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortDirection((direction) => (direction === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(field);
      setSortDirection('asc');
    }
  };

  const clearFilters = () => {
    setSearch('');
    setSubmittedSearch('');
    setStatusFilter('');
    setTypeFilter('');
    setLocationFilter('');
  };

  const sortableHeading = (field, label) => (
    <TableSortLabel
      active={sortBy === field}
      direction={sortBy === field ? sortDirection : 'asc'}
      onClick={() => handleSort(field)}
    >
      {label}
    </TableSortLabel>
  );

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

        <Box component="form" onSubmit={handleSearchSubmit} sx={{ mb: 1.5 }}>
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

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel id="job-status-filter-label">Status</InputLabel>
            <Select
              labelId="job-status-filter-label"
              label="Status"
              onChange={(event) => setStatusFilter(event.target.value)}
              value={statusFilter}
            >
              <MenuItem value="">All statuses</MenuItem>
              {filterOptions.statuses.map((status) => (
                <MenuItem key={status} value={status}>{titleize(status)}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 170 }}>
            <InputLabel id="job-type-filter-label">Employment type</InputLabel>
            <Select
              labelId="job-type-filter-label"
              label="Employment type"
              onChange={(event) => setTypeFilter(event.target.value)}
              value={typeFilter}
            >
              <MenuItem value="">All types</MenuItem>
              {filterOptions.types.map((type) => (
                <MenuItem key={type} value={type}>{titleize(type)}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel id="job-location-filter-label">Location</InputLabel>
            <Select
              labelId="job-location-filter-label"
              label="Location"
              onChange={(event) => setLocationFilter(event.target.value)}
              value={locationFilter}
            >
              <MenuItem value="">All locations</MenuItem>
              {filterOptions.locations.map((location) => (
                <MenuItem key={location} value={location}>{location}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button disabled={!hasActiveFilters} onClick={clearFilters}>Clear filters</Button>
        </Stack>

        {isLoading ? <CircularProgress aria-label="Loading jobs" /> : null}

        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{sortableHeading('title', 'Title')}</TableCell>
              <TableCell>{sortableHeading('status', 'Status')}</TableCell>
              <TableCell>{sortableHeading('employment_type', 'Type')}</TableCell>
              <TableCell>{sortableHeading('location', 'Location')}</TableCell>
              <TableCell>{sortableHeading('salary', 'Salary')}</TableCell>
              <TableCell>{sortableHeading('created_at', 'Created')}</TableCell>
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
                <TableCell colSpan={7}>{hasActiveFilters ? 'No jobs match your search and filters.' : 'No jobs yet.'}</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
