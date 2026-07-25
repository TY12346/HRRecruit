import { useEffect, useState } from 'react';
import {

  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
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
import { getInterviewEvaluationDetail, getInterviews } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

function EvaluationCard({ evaluation }) {
  return (
    <Card variant="outlined" sx={{ mt: 2 }}>
      <CardContent>
        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
          {evaluation.interviewer_name || 'Interviewer evaluation'}
        </Typography>
        <Typography>
          <strong>Total score:</strong> {evaluation.total_score ?? 'Not submitted'}
        </Typography>
        <Typography>
          <strong>Overall comment:</strong> {evaluation.overall_comment || '—'}
        </Typography>
        <List dense>
          {evaluation.answers?.map((answer) => (
            <ListItem key={answer.id} disableGutters>
              <ListItemText
                primary={`${answer.criterion?.criterion_name}: ${answer.score}`}
                secondary={answer.comment || answer.criterion?.description}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}

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
        ? names.map((name, index) => (
          <Typography key={`${name}-${index}`} component="span" display="block">
            {name}
          </Typography>
        ))
        : '—'}
    </TableCell>
  );
}

export default function InterviewEvaluationDetailPage() {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('job_id');
  const [interviews, setInterviews] = useState([]);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getInterviews(jobId ? { job_id: jobId } : {})
      .then(setInterviews)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load interviews.')))
      .finally(() => setIsLoading(false));
  }, [jobId]);

  const openDetail = async (interview) => {
    setDetail(null);
    setError('');
    try {
      setDetail(await getInterviewEvaluationDetail(interview.id));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Evaluation detail is not available yet.'));
    }
  };

  const submittedEvaluations = detail?.evaluations ?? (detail?.evaluation ? [detail.evaluation] : []);

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
                      <Button onClick={() => openDetail(interview)} size="small" variant="outlined">View evaluations</Button>
                      <Button component={RouterLink} size="small" to={`/recruiter/jobs/${interview.application?.job}/hiring-decision`}>Job decision</Button>
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

        <Stack spacing={2} sx={{ mt: 2 }}>
          {detail ? (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {detail.applicant_name || 'Applicant'} — {detail.job_title || 'Job'}
              </Typography>
              <Typography variant="h6" sx={{ mt: 2 }}>Submitted evaluations</Typography>
              {submittedEvaluations.length ? (
                submittedEvaluations.map((evaluation) => <EvaluationCard key={evaluation.id} evaluation={evaluation} />)
              ) : (
                <Typography color="text.secondary">No interviewer evaluations submitted yet.</Typography>
              )}
              <Typography variant="h6" sx={{ mt: 2 }}>AI summary</Typography>
              <Typography>{detail.ai_summary?.editable_summary_text || detail.ai_summary?.summary_text || 'No AI summary generated yet.'}</Typography>
              <Typography variant="h6" sx={{ mt: 2 }}>Transcript</Typography>
              <Typography whiteSpace="pre-line">{detail.transcript?.transcript_text || 'No transcript uploaded yet.'}</Typography>
            </Paper>
          ) : null}
        </Stack>
      </Paper>
    </Box>
  );
}
