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

export default function AssignedApplicantsPage() {
  const [interviews, setInterviews] = useState([]);
  const [search, setSearch] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getAssignedInterviews()
      .then(setInterviews)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load assigned applicants.')))
      .finally(() => setIsLoading(false));
  }, []);

  const filteredInterviews = useMemo(() => {
    const query = submittedSearch.trim().toLowerCase();
    return interviews.filter((interview) => {
      const status = interview.application?.status ?? '';
      const matchesStatus = statusFilter === 'all' || status === statusFilter;
      const matchesSearch = !query || [applicantName(interview), jobTitle(interview), interview.application?.recruiter_remark]
        .some((value) => String(value ?? '').toLowerCase().includes(query));
      return matchesStatus && matchesSearch;
    });
  }, [interviews, statusFilter, submittedSearch]);

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
            Assigned Applicants
          </Typography>
          <Typography color="text.secondary">
            Review applicants assigned to your interviews and open their details when needed.
          </Typography>
        </Stack>

        <Box component="form" onSubmit={handleSearchSubmit} sx={{ mb: 2 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <TextField
              fullWidth
              label="Search by applicant name, job, or remark"
              onChange={(event) => setSearch(event.target.value)}
              value={search}
            />
            <TextField
              select
              label="Status"
              onChange={(event) => setStatusFilter(event.target.value)}
              sx={{ minWidth: { sm: 190 } }}
              value={statusFilter}
            >
              <MenuItem value="all">All statuses</MenuItem>
              <MenuItem value="shortlisted">Shortlisted</MenuItem>
              <MenuItem value="interview_invited">Interview invited</MenuItem>
              <MenuItem value="interview_scheduled">Interview scheduled</MenuItem>
              <MenuItem value="evaluation_submitted">Evaluation submitted</MenuItem>
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
                <TableCell>Panel</TableCell>
                <TableCell>Recruiter remark</TableCell>
                <TableCell align="right">Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredInterviews.map((interview) => (
                <TableRow key={interview.id}>
                  <TableCell>{applicantName(interview)}</TableCell>
                  <TableCell>{jobTitle(interview)}</TableCell>
                  <TableCell>{titleize(interview.application?.status)}</TableCell>
                  <TableCell>{formatDateTime(interview.scheduled_datetime)}</TableCell>
                  <TableCell>{panelInterviewerNames(interview)}</TableCell>
                  <TableCell>{interview.application?.recruiter_remark || '—'}</TableCell>
                  <TableCell align="right">
                    <Button component={RouterLink} size="small" to={`/interviewer/applicants/${interview.application?.id}`} variant="outlined">
                      Applicant detail
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!isLoading && filteredInterviews.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7}>No assigned applicants found.</TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </Box>
      </Paper>
    </Box>
  );
}
