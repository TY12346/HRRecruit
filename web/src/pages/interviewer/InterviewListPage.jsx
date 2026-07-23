import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  MenuItem,
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
import { Link as RouterLink } from 'react-router-dom';
import { getAssignedInterviews } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { applicantName, formatDateTime, getApiErrorMessage, jobTitle, panelInterviewerNames, titleize } from './interviewerUtils.js';

export default function InterviewListPage() {
  const [interviews, setInterviews] = useState([]);
  const [search, setSearch] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [modeFilter, setModeFilter] = useState('all');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getAssignedInterviews()
      .then(setInterviews)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load interviews.')))
      .finally(() => setIsLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const query = submittedSearch.trim().toLowerCase();
    return interviews.filter((interview) => {
      const matchesStatus = filter === 'all' || (filter === 'upcoming' ? ['assigned', 'scheduled'].includes(interview.status) : interview.status === filter);
      const matchesMode = modeFilter === 'all' || interview.mode === modeFilter;
      const matchesSearch = !query || [applicantName(interview), jobTitle(interview), interview.meeting_link, interview.location]
        .some((value) => String(value ?? '').toLowerCase().includes(query));
      return matchesStatus && matchesMode && matchesSearch;
    });
  }, [filter, interviews, modeFilter, submittedSearch]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setSubmittedSearch(search);
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Stack spacing={0.5} sx={{ mb: 3 }}>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
            Interviews
          </Typography>
          <Typography color="text.secondary">
            Review your scheduled interviews and open the details to prepare for each session.
          </Typography>
        </Stack>

        <Box component="form" onSubmit={handleSearchSubmit} sx={{ mb: 2 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <TextField
              fullWidth
              label="Search by applicant, job, or venue"
              onChange={(event) => setSearch(event.target.value)}
              value={search}
            />
            <TextField
              select
              label="Status"
              onChange={(event) => setFilter(event.target.value)}
              sx={{ minWidth: { sm: 180 } }}
              value={filter}
            >
              <MenuItem value="all">All statuses</MenuItem>
              <MenuItem value="upcoming">Upcoming</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="declined">Declined</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
            </TextField>
            <TextField
              select
              label="Mode"
              onChange={(event) => setModeFilter(event.target.value)}
              sx={{ minWidth: { sm: 160 } }}
              value={modeFilter}
            >
              <MenuItem value="all">All modes</MenuItem>
              <MenuItem value="online">Online</MenuItem>
              <MenuItem value="physical">Physical</MenuItem>
              <MenuItem value="phone">Phone</MenuItem>
            </TextField>
            <Button type="submit" variant="outlined">Search</Button>
          </Stack>
        </Box>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        <Box sx={{ overflowX: 'auto' }}>
          <Table sx={{ mt: 2, minWidth: 940 }}>
            <TableHead>
              <TableRow>
                <TableCell>Applicant</TableCell>
                <TableCell>Job applied</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Scheduled</TableCell>
                <TableCell>Mode</TableCell>
                <TableCell>Panel</TableCell>
                <TableCell>Venue</TableCell>
                <TableCell align="right">Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.map((interview) => (
                <TableRow key={interview.id}>
                  <TableCell>{applicantName(interview)}</TableCell>
                  <TableCell>{jobTitle(interview)}</TableCell>
                  <TableCell>{titleize(interview.status)}</TableCell>
                  <TableCell>{formatDateTime(interview.scheduled_datetime)}</TableCell>
                  <TableCell>{titleize(interview.mode)}</TableCell>
                  <TableCell>{panelInterviewerNames(interview)}</TableCell>
                  <TableCell>{interview.meeting_link || interview.location || 'No venue yet'}</TableCell>
                  <TableCell align="right">
                    <Button component={RouterLink} size="small" to={`/interviewer/interviews/${interview.id}`} variant="outlined">
                      View detail
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!isLoading && filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8}>No interviews found.</TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </Box>
      </Paper>
    </Box>
  );
}
