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
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink } from 'react-router-dom';
import { cancelJobRequisition, getJobRequisitions } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

const departmentName = (item) => (item.department === 'Other' ? item.custom_department : item.department) || '—';

const sortValues = {
  title: (item) => item.title ?? '',
  department: departmentName,
  location: (item) => item.location ?? '',
  employment_type: (item) => item.employment_type ?? '',
  position_status: (item) => item.position_status ?? '',
  status: (item) => item.status ?? '',
  created_at: (item) => new Date(item.created_at).getTime(),
};

export default function JobRequisitionsPage() {
  const [requisitions, setRequisitions] = useState([]);
  const [search, setSearch] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState('');
  const [positionStatusFilter, setPositionStatusFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const cancelRequisition = async (item) => {
    if (!window.confirm(`Cancel the job requisition for ${item.title}?`)) return;
    setBusyId(item.id);
    setError('');
    try {
      const updated = await cancelJobRequisition(item.id);
      setRequisitions((current) => current.map((requisition) => requisition.id === updated.id ? updated : requisition));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to cancel job requisition.'));
    } finally {
      setBusyId(null);
    }
  };

  useEffect(() => {
    getJobRequisitions()
      .then(setRequisitions)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load job requisitions.')))
      .finally(() => setIsLoading(false));
  }, []);

  const filterOptions = useMemo(() => ({
    departments: [...new Set(requisitions.map(departmentName).filter((value) => value !== '—'))].sort(),
    locations: [...new Set(requisitions.map((item) => item.location).filter(Boolean))].sort(),
    employmentTypes: [...new Set(requisitions.map((item) => item.employment_type).filter(Boolean))].sort(),
    positionStatuses: [...new Set(requisitions.map((item) => item.position_status).filter(Boolean))].sort(),
    statuses: [...new Set(requisitions.map((item) => item.status).filter(Boolean))].sort(),
  }), [requisitions]);

  const visibleRequisitions = useMemo(() => {
    const searchTerm = submittedSearch.trim().toLowerCase();
    const filteredRequisitions = requisitions.filter((item) => (
      (!searchTerm || [
        item.title,
        departmentName(item),
        item.location,
        item.employment_type,
        item.position_status,
        item.status,
      ].some((value) => String(value ?? '').toLowerCase().includes(searchTerm)))
      && (!departmentFilter || departmentName(item) === departmentFilter)
      && (!locationFilter || item.location === locationFilter)
      && (!employmentTypeFilter || item.employment_type === employmentTypeFilter)
      && (!positionStatusFilter || item.position_status === positionStatusFilter)
      && (!statusFilter || item.status === statusFilter)
    ));

    const valueFor = sortValues[sortBy];
    return [...filteredRequisitions].sort((firstItem, secondItem) => {
      const firstValue = valueFor(firstItem);
      const secondValue = valueFor(secondItem);
      const comparison = typeof firstValue === 'string'
        ? firstValue.localeCompare(secondValue, undefined, { numeric: true, sensitivity: 'base' })
        : firstValue - secondValue;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [
    requisitions,
    submittedSearch,
    departmentFilter,
    locationFilter,
    employmentTypeFilter,
    positionStatusFilter,
    statusFilter,
    sortBy,
    sortDirection,
  ]);

  const hasActiveFilters = Boolean(
    submittedSearch
    || departmentFilter
    || locationFilter
    || employmentTypeFilter
    || positionStatusFilter
    || statusFilter,
  );

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
    setDepartmentFilter('');
    setLocationFilter('');
    setEmploymentTypeFilter('');
    setPositionStatusFilter('');
    setStatusFilter('');
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

        <Box component="form" onSubmit={handleSearchSubmit} sx={{ mb: 1.5 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <TextField
              fullWidth
              label="Search by title, department, location, or status"
              onChange={(event) => setSearch(event.target.value)}
              value={search}
            />
            <Button type="submit" variant="outlined">Search</Button>
          </Stack>
        </Box>

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} useFlexGap flexWrap="wrap" sx={{ mb: 2 }}>
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel id="requisition-department-filter-label">Department</InputLabel>
            <Select labelId="requisition-department-filter-label" label="Department" value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)}>
              <MenuItem value="">All departments</MenuItem>
              {filterOptions.departments.map((department) => <MenuItem key={department} value={department}>{department}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel id="requisition-location-filter-label">Location</InputLabel>
            <Select labelId="requisition-location-filter-label" label="Location" value={locationFilter} onChange={(event) => setLocationFilter(event.target.value)}>
              <MenuItem value="">All locations</MenuItem>
              {filterOptions.locations.map((location) => <MenuItem key={location} value={location}>{location}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 175 }}>
            <InputLabel id="requisition-employment-type-filter-label">Employment type</InputLabel>
            <Select labelId="requisition-employment-type-filter-label" label="Employment type" value={employmentTypeFilter} onChange={(event) => setEmploymentTypeFilter(event.target.value)}>
              <MenuItem value="">All employment types</MenuItem>
              {filterOptions.employmentTypes.map((type) => <MenuItem key={type} value={type}>{titleize(type)}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 165 }}>
            <InputLabel id="requisition-position-status-filter-label">Position status</InputLabel>
            <Select labelId="requisition-position-status-filter-label" label="Position status" value={positionStatusFilter} onChange={(event) => setPositionStatusFilter(event.target.value)}>
              <MenuItem value="">All position statuses</MenuItem>
              {filterOptions.positionStatuses.map((status) => <MenuItem key={status} value={status}>{titleize(status)}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 145 }}>
            <InputLabel id="requisition-status-filter-label">Status</InputLabel>
            <Select labelId="requisition-status-filter-label" label="Status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <MenuItem value="">All statuses</MenuItem>
              {filterOptions.statuses.map((status) => <MenuItem key={status} value={status}>{titleize(status)}</MenuItem>)}
            </Select>
          </FormControl>
          <Button disabled={!hasActiveFilters} onClick={clearFilters}>Clear filters</Button>
        </Stack>

        {isLoading ? <CircularProgress aria-label="Loading job requisitions" /> : null}

        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{sortableHeading('title', 'Title')}</TableCell>
              <TableCell>{sortableHeading('department', 'Department')}</TableCell>
              <TableCell>{sortableHeading('location', 'Location')}</TableCell>
              <TableCell>{sortableHeading('employment_type', 'Employment type')}</TableCell>
              <TableCell>{sortableHeading('position_status', 'Position status')}</TableCell>
              <TableCell>{sortableHeading('status', 'Status')}</TableCell>
              <TableCell>{sortableHeading('created_at', 'Submitted')}</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleRequisitions.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <Typography sx={{ fontWeight: 700 }}>{item.title}</Typography>
                </TableCell>
                <TableCell>{departmentName(item)}</TableCell>
                <TableCell>{item.location || '—'}</TableCell>
                <TableCell>{titleize(item.employment_type)}</TableCell>
                <TableCell>{titleize(item.position_status)}</TableCell>
                <TableCell>
                  <Chip label={titleize(item.status)} size="small" color={item.status === 'approved' ? 'success' : item.status === 'rejected' ? 'error' : 'warning'} />
                </TableCell>
                <TableCell>{formatDateTime(item.created_at)}</TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    {item.status === 'rejected' ? (
                      <Button component={RouterLink} to={`/recruiter/job-requisitions/${item.id}/edit`} size="small">Edit and resubmit</Button>
                    ) : null}
                    {['pending', 'rejected'].includes(item.status) ? (
                      <Button color="error" disabled={busyId === item.id} onClick={() => cancelRequisition(item)} size="small">Cancel</Button>
                    ) : null}
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && visibleRequisitions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8}>{hasActiveFilters ? 'No job requisitions match your search and filters.' : 'No job requisitions yet.'}</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
