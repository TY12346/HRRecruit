import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Paper, Stack, TextField, Typography } from '@mui/material';
import { useParams } from 'react-router-dom';
import { getInterview, submitInterviewEvaluation } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { candidateName, getApiErrorMessage, jobTitle } from './interviewerUtils.js';

const emptyAnswerForCriterion = (criterion) => ({
  criterion_id: criterion.id,
  score: '',
  comment: '',
});

export default function SubmitEvaluationPage() {
  const { interviewId } = useParams();
  const [interview, setInterview] = useState(null);
  const [overallComment, setOverallComment] = useState('');
  const [answers, setAnswers] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const criteria = useMemo(() => interview?.evaluation_criteria ?? [], [interview]);

  useEffect(() => {
    getInterview(interviewId)
      .then((data) => {
        setInterview(data);
        setAnswers((data.evaluation_criteria ?? []).map(emptyAnswerForCriterion));
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load interview.')));
  }, [interviewId]);

  const updateAnswer = (criterionId, patch) => {
    setAnswers((current) => current.map((answer) => (
      answer.criterion_id === criterionId ? { ...answer, ...patch } : answer
    )));
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setIsSaving(true);

    try {
      await submitInterviewEvaluation(interviewId, {
        overall_comment: overallComment,
        answers: answers.map((answer) => ({
          criterion_id: answer.criterion_id,
          score: answer.score,
          comment: answer.comment,
        })),
      });
      setSuccess('Evaluation submitted successfully.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to submit evaluation. Please complete every rubric score within its allowed maximum.'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Submit Evaluation</Typography>
        {interview ? (
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {candidateName(interview)} • {jobTitle(interview)}
          </Typography>
        ) : null}

        <Alert severity="info" sx={{ mb: 2 }}>
          Complete each recruiter-configured evaluation criterion below. The criterion IDs are handled automatically.
        </Alert>
        {criteria.length === 0 && interview ? (
          <Alert severity="warning" sx={{ mb: 2 }}>
            This job does not have an interview evaluation form configured yet. Ask the recruiter to set up the form before submitting an evaluation.
          </Alert>
        ) : null}
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}

        <Stack component="form" spacing={2} onSubmit={submit}>
          <TextField
            label="Overall comment"
            multiline
            minRows={4}
            required
            value={overallComment}
            onChange={(event) => setOverallComment(event.target.value)}
          />

          {criteria.map((criterion, index) => {
            const answer = answers.find((item) => item.criterion_id === criterion.id) ?? emptyAnswerForCriterion(criterion);
            return (
              <Card key={criterion.id} variant="outlined">
                <CardContent>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {index + 1}. {criterion.criterion_name}
                      </Typography>
                      {criterion.description ? (
                        <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                          {criterion.description}
                        </Typography>
                      ) : null}
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        Maximum score: {criterion.max_score} • Weight: {criterion.weight_score}
                      </Typography>
                    </Box>
                    <TextField
                      label={`Score out of ${criterion.max_score}`}
                      type="number"
                      required
                      value={answer.score}
                      inputProps={{ min: 0, max: Number(criterion.max_score), step: '0.01' }}
                      onChange={(event) => updateAnswer(criterion.id, { score: event.target.value })}
                    />
                    <TextField
                      label="Criterion comment"
                      multiline
                      minRows={2}
                      value={answer.comment}
                      onChange={(event) => updateAnswer(criterion.id, { comment: event.target.value })}
                    />
                  </Stack>
                </CardContent>
              </Card>
            );
          })}

          <Button type="submit" variant="contained" disabled={isSaving || criteria.length === 0} sx={{ alignSelf: 'flex-start' }}>
            {isSaving ? 'Submitting…' : 'Submit evaluation'}
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
