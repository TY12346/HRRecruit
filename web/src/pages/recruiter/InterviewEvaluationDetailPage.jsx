import { useEffect, useState } from 'react';
import {

  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink } from 'react-router-dom';
import { getInterviewEvaluationDetail, getInterviews } from '../../api/client.js';
import ApplicantJobSummary from '../../components/ApplicantJobSummary.jsx';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage } from './recruiterUtils.js';

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

export default function InterviewEvaluationDetailPage() {
  const [interviews, setInterviews] = useState([]);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getInterviews()
      .then(setInterviews)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load interviews.')))
      .finally(() => setIsLoading(false));
  }, []);

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
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Interview evaluations</Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        <Stack spacing={2}>
          {interviews.map((interview) => (
            <Card key={interview.id}>
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
                  <Box>
                    <ApplicantJobSummary applicantName={interview.application?.applicant?.full_name} jobTitle={interview.application?.job_title} variant="h6" />
                    <Typography color="text.secondary">
                      {interview.interviewer?.full_name} • {formatDateTime(interview.scheduled_datetime)} • {interview.status}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1}>
                    <Button onClick={() => openDetail(interview)} variant="outlined">View evaluations</Button>
                    <Button component={RouterLink} to={`/recruiter/jobs/${interview.application?.job}/hiring-decision`}>Job decision</Button>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          ))}
          {detail ? (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <ApplicantJobSummary applicantName={detail.applicant_name} jobTitle={detail.job_title} variant="h6" />
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
