import { useEffect, useState } from 'react';
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
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { getInterviews } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

function interviewerNames(interview) {
  const assignedInterviewers = [
    interview.interviewer,
    ...(interview.panel_interviewers ?? []),
  ];
  const uniqueInterviewers = new Map(
    assignedInterviewers
      .filter(Boolean)
      .map((interviewer) => [interviewer.id ?? interviewer.full_name, interviewer]),
  );

  return [...uniqueInterviewers.values()]
    .map((interviewer) => interviewer.full_name)
    .filter(Boolean);
}

function InterviewerCell({ interview }) {
  const names = interviewerNames(interview);

  return (
    <TableCell>
      {names.length
        ? <Stack spacing={0.75} alignItems="flex-start">
          {names.map((name, index) => (
            <Chip key={`${name}-${index}`} label={name} size="small" variant="outlined" />
          ))}
        </Stack>
        : '—'}
    </TableCell>
  );
}

export default function InterviewEvaluationDetailPage() {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('job_id');
  const [interviews, setInterviews] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getInterviews(jobId ? { job_id: jobId } : {})
      .then(setInterviews)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load interviews.')))
      .finally(() => setIsLoading(false));
  }, [jobId]);

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Stack spacing={0.5} sx={{ mb: 3 }}>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
            {jobId ? 'Job interviews' : 'Interview evaluations'}
          </Typography>
          <Typography color="text.secondary">
            {jobId ? 'Review every interview for this job, regardless of its status.' : 'Review interviewer evaluations and continue to the job hiring decision when ready.'}
          </Typography>
        </Stack>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        <Box sx={{ overflowX: 'auto' }}>
          <Table sx={{ mt: 2, minWidth: 900 }}>
            <TableHead>
              <TableRow>
                <TableCell>Applicant</TableCell>
                <TableCell>Job applied</TableCell>
                <TableCell>Interviewer</TableCell>
                <TableCell>Scheduled</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {interviews.map((interview) => (
                <TableRow key={interview.id}>
                  <TableCell>{interview.application?.applicant?.full_name || '—'}</TableCell>
                  <TableCell>{interview.application?.job_title || '—'}</TableCell>
                  <InterviewerCell interview={interview} />
                  <TableCell>{formatDateTime(interview.scheduled_datetime)}</TableCell>
                  <TableCell>
                    {titleize(interview.status)}
                    {interview.availability_alert ? (
                      <Chip
                        color="warning"
                        label="No common availability"
                        size="small"
                        sx={{ display: 'flex', mt: 0.5, width: 'fit-content' }}
                        title={interview.availability_alert}
                      />
                    ) : null}
                  </TableCell>
                  <TableCell align="right">
                    <Stack direction="row" justifyContent="flex-end" spacing={1}>
                      <Button
                        component={RouterLink}
                        size="small"
                        to={`/recruiter/applications/${interview.application?.id}`}
                        variant="outlined"
                      >
                        View applicant profile
                      </Button>
                      {interview.status === 'evaluation_submitted' ? (
                        <Button
                          component={RouterLink}
                          to={`/recruiter/interviews/${interview.id}/evaluations${jobId ? `?job_id=${encodeURIComponent(jobId)}` : ''}`}
                          size="small"
                          variant="outlined"
                        >
                          View evaluations
                        </Button>
                      ) : null}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
              {!isLoading && interviews.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6}>No interviews found.</TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </Box>
      </Paper>
    </Box>
  );
}
