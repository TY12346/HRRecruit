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
import { Link as RouterLink, useParams, useSearchParams } from 'react-router-dom';
import { getInterviewEvaluationDetail } from '../../api/client.js';
import Alert from '../../components/TimedAlert.jsx';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';

function EvaluationCard({ evaluation }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
          {evaluation.interviewer_name || 'Interviewer evaluation'}
        </Typography>
        <Typography><strong>Total score:</strong> {evaluation.total_score ?? 'Not submitted'}</Typography>
        <Typography><strong>Overall comment:</strong> {evaluation.overall_comment || '—'}</Typography>
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

export default function InterviewEvaluationsPage() {
  const { interviewId } = useParams();
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('job_id');
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getInterviewEvaluationDetail(interviewId)
      .then(setDetail)
      .catch((err) => setError(getApiErrorMessage(err, 'Evaluation detail is not available yet.')))
      .finally(() => setIsLoading(false));
  }, [interviewId]);

  const submittedEvaluations = detail?.evaluations ?? (detail?.evaluation ? [detail.evaluation] : []);
  const interviewsUrl = `/recruiter/interviews${jobId ? `?job_id=${encodeURIComponent(jobId)}` : ''}`;

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Button component={RouterLink} to={interviewsUrl} variant="outlined" sx={{ mb: 2 }}>
          Back to job interviews
        </Button>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
          Interview evaluations
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Review submitted scorecards, the AI summary, audio, and transcript for this interview.
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        {detail ? (
          <Stack spacing={3}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {detail.applicant_name || 'Applicant'} — {detail.job_title || 'Job'}
            </Typography>

            <Box>
              <Typography variant="h6" sx={{ mb: 1 }}>Submitted evaluations</Typography>
              <Stack spacing={2}>
                {submittedEvaluations.length
                  ? submittedEvaluations.map((evaluation) => <EvaluationCard key={evaluation.id} evaluation={evaluation} />)
                  : <Typography color="text.secondary">No interviewer evaluations submitted yet.</Typography>}
              </Stack>
            </Box>

            <Box>
              <Typography variant="h6" sx={{ mb: 1 }}>AI summary</Typography>
              {detail.ai_summary ? (
                <Stack spacing={0.75}>
                  <Typography whiteSpace="pre-line">{detail.ai_summary.editable_summary_text}</Typography>
                  <Typography><strong>Strengths:</strong> {detail.ai_summary.strengths || '—'}</Typography>
                  <Typography><strong>Weaknesses:</strong> {detail.ai_summary.weaknesses || '—'}</Typography>
                  <Typography><strong>Communication score:</strong> {detail.ai_summary.communication_score ?? '—'}</Typography>
                  <Typography><strong>Overall impression:</strong> {detail.ai_summary.overall_impression || '—'}</Typography>
                </Stack>
              ) : <Typography>No AI summary generated yet.</Typography>}
            </Box>

            <Box>
              <Typography variant="h6">Interview audio</Typography>
              {detail.transcript?.audio_url ? (
                <Box component="audio" controls preload="metadata" src={detail.transcript.audio_url} sx={{ width: '100%', mt: 1 }}>
                  Your browser does not support audio playback.
                </Box>
              ) : <Typography color="text.secondary">No interview audio uploaded.</Typography>}
            </Box>

            <Box>
              <Typography variant="h6" sx={{ mb: 1 }}>Transcript</Typography>
              <Typography whiteSpace="pre-line">
                {detail.transcript?.speaker_labelled_transcript || detail.transcript?.transcript_text || 'No transcript generated yet.'}
              </Typography>
            </Box>
          </Stack>
        ) : null}
      </Paper>
    </Box>
  );
}
