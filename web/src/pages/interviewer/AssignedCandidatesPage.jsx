import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, CircularProgress, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getAssignedInterviews } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { candidateName, formatDateTime, getApiErrorMessage, jobTitle, panelInterviewerNames, titleize } from './interviewerUtils.js';

export default function AssignedCandidatesPage() {
  const [interviews, setInterviews] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getAssignedInterviews()
      .then(setInterviews)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load assigned candidates.')))
      .finally(() => setIsLoading(false));
  }, []);

  const filteredInterviews = useMemo(() => {
    const query = search.trim().toLowerCase();
    return interviews.filter((interview) => {
      const status = interview.application?.status ?? '';
      const matchesStatus = statusFilter === 'all' || status === statusFilter;
      const matchesSearch = !query || [candidateName(interview), jobTitle(interview), interview.application?.recruiter_remark]
        .some((value) => String(value ?? '').toLowerCase().includes(query));
      return matchesStatus && matchesSearch;
    });
  }, [interviews, search, statusFilter]);

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 2 }}>Assigned Candidates</Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
          <TextField label="Search candidates" value={search} onChange={(event) => setSearch(event.target.value)} fullWidth />
          <TextField select label="Status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} sx={{ minWidth: 180 }}>
            <MenuItem value="all">All statuses</MenuItem>
            <MenuItem value="shortlisted">Shortlisted</MenuItem>
            <MenuItem value="interview_invited">Interview invited</MenuItem>
            <MenuItem value="interview_scheduled">Interview scheduled</MenuItem>
            <MenuItem value="evaluation_submitted">Evaluation submitted</MenuItem>
          </TextField>
        </Stack>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        <Stack spacing={0} sx={{ mt: 3, mx: { xs: 0, md: 2 } }}>
          {filteredInterviews.map((interview) => (
            <Stack key={interview.id} direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1} sx={{ py: 1, borderTop: '1px solid', borderColor: 'divider', width: '100%', '&:first-of-type': { borderTop: 0 } }}>
              <Box>
                <Typography sx={{ fontWeight: 700 }}>{candidateName(interview)} • {jobTitle(interview)}</Typography>
                <Typography color="text.secondary" variant="body2">
                  {titleize(interview.application?.status)} • Scheduled: {formatDateTime(interview.scheduled_datetime)} • Panel: {panelInterviewerNames(interview)} • Remark: {interview.application?.recruiter_remark || '—'}
                </Typography>
              </Box>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ ml: { md: 'auto' }, justifyContent: 'flex-end' }}>
                <Button component={RouterLink} to={`/interviewer/candidates/${interview.application?.id}`} variant="outlined" size="small">Candidate detail</Button>
              </Stack>
            </Stack>
          ))}
          {!isLoading && filteredInterviews.length === 0 ? <Typography color="text.secondary">No assigned candidates found.</Typography> : null}
        </Stack>
      </Paper>
    </Box>
  );
}
