import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, CircularProgress, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getAssignedInterviews } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import ApplicantJobSummary from '../../components/ApplicantJobSummary.jsx';
import { applicantName, formatDateTime, getApiErrorMessage, jobTitle, panelInterviewerNames, titleize } from './interviewerUtils.js';

export default function InterviewListPage() {
  const [interviews, setInterviews] = useState([]);
  const [search, setSearch] = useState('');
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
    const query = search.trim().toLowerCase();
    return interviews.filter((interview) => {
      const matchesStatus = filter === 'all' || (filter === 'upcoming' ? ['assigned', 'scheduled'].includes(interview.status) : interview.status === filter);
      const matchesMode = modeFilter === 'all' || interview.mode === modeFilter;
      const matchesSearch = !query || [applicantName(interview), jobTitle(interview), interview.meeting_link, interview.location]
        .some((value) => String(value ?? '').toLowerCase().includes(query));
      return matchesStatus && matchesMode && matchesSearch;
    });
  }, [filter, interviews, modeFilter, search]);

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 2 }}>Interviews</Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
          <TextField label="Search interviews" value={search} onChange={(event) => setSearch(event.target.value)} fullWidth />
          <TextField select label="Status" value={filter} onChange={(event) => setFilter(event.target.value)} sx={{ minWidth: 180 }}>
            <MenuItem value="all">All statuses</MenuItem>
            <MenuItem value="upcoming">Upcoming</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="declined">Declined</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
          </TextField>
          <TextField select label="Mode" value={modeFilter} onChange={(event) => setModeFilter(event.target.value)} sx={{ minWidth: 160 }}>
            <MenuItem value="all">All modes</MenuItem>
            <MenuItem value="online">Online</MenuItem>
            <MenuItem value="physical">Physical</MenuItem>
            <MenuItem value="phone">Phone</MenuItem>
          </TextField>
        </Stack>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        <Stack spacing={0} sx={{ mt: 3, mx: { xs: 0, md: 2 } }}>
          {filtered.map((interview) => (
            <Stack key={interview.id} direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1} sx={{ py: 1, borderTop: '1px solid', borderColor: 'divider', width: '100%', '&:first-of-type': { borderTop: 0 } }}>
              <Box>
                <ApplicantJobSummary applicantName={applicantName(interview)} jobTitle={jobTitle(interview)} />
                <Typography color="text.secondary" variant="body2">
                  {titleize(interview.status)} • Panel: {panelInterviewerNames(interview)} • {formatDateTime(interview.scheduled_datetime)} • {titleize(interview.mode)} • {interview.meeting_link || interview.location || 'No venue yet'}
                </Typography>
              </Box>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ ml: { md: 'auto' }, justifyContent: 'flex-end' }}>
                <Button component={RouterLink} to={`/interviewer/interviews/${interview.id}`} variant="outlined" size="small">View detail</Button>
              </Stack>
            </Stack>
          ))}
          {!isLoading && filtered.length === 0 ? <Typography color="text.secondary">No interviews found.</Typography> : null}
        </Stack>
      </Paper>
    </Box>
  );
}
