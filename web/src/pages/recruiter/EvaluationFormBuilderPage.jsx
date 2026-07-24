import { useEffect, useState } from 'react';
import { Box, Button, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useNavigate, useParams } from 'react-router-dom';
import { createInterviewEvaluationScorecard, getJob } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import {
  applyCriterionImportance,
  cloneCriterion,
  criterionImportanceOptions,
  hydrateCriterion,
  prepareCriteriaForApi,
} from './evaluationScoring.js';
import { getApiErrorMessage } from './recruiterUtils.js';

export default function EvaluationFormBuilderPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [title, setTitle] = useState('Interview Evaluation Scorecard');
  const [criteria, setCriteria] = useState([cloneCriterion()]);
  const [existing, setExisting] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    getJob(jobId)
      .then((job) => {
        const scorecard = job.interview_evaluation_scorecard ?? job.interview_evaluation_form;
        if (scorecard) {
          setExisting(scorecard);
          setTitle(scorecard.title);
          setCriteria((scorecard.criteria ?? []).map(hydrateCriterion));
        }
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load evaluation scorecard.')));
  }, [jobId]);

  const update = (index, field, value) => {
    setCriteria((items) => items.map((item, itemIndex) => {
      if (itemIndex !== index) {
        return item;
      }
      if (field === 'importance_level') {
        return applyCriterionImportance(item, value);
      }
      return { ...item, [field]: value };
    }));
  };

  const save = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    try {
      const payloadCriteria = prepareCriteriaForApi(criteria);
      const saved = await createInterviewEvaluationScorecard(jobId, { title, criteria: payloadCriteria });
      setSuccess(existing ? 'Evaluation scorecard updated.' : 'Evaluation scorecard created.');
      setExisting(saved);
      setCriteria((saved.criteria ?? payloadCriteria).map(hydrateCriterion));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to save evaluation scorecard.'));
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Evaluation scorecard builder</Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        <Box component="form" onSubmit={save}>
          <Stack spacing={2}>
            <TextField label="Scorecard title" value={title} onChange={(event) => setTitle(event.target.value)} />
            {criteria.map((criterion, index) => (
              <Paper key={index} variant="outlined" sx={{ p: 2 }}>
                <Stack spacing={2}>
                  <TextField
                    label="Criterion name"
                    required
                    value={criterion.criterion_name}
                    onChange={(event) => update(index, 'criterion_name', event.target.value)}
                  />
                  <TextField
                    label="Description"
                    required
                    value={criterion.description}
                    onChange={(event) => update(index, 'description', event.target.value)}
                  />
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                    <TextField
                      label="Max score"
                      type="number"
                      value={criterion.max_score}
                      onChange={(event) => update(index, 'max_score', event.target.value)}
                    />
                    <TextField
                      label="Interview scoring importance"
                      select
                      value={criterion.importance_level}
                      onChange={(event) => update(index, 'importance_level', event.target.value)}
                    >
                      {criterionImportanceOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label} — {option.description}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Stack>
                  <Button
                    color="error"
                    disabled={criteria.length === 1}
                    onClick={() => setCriteria((items) => items.filter((_, itemIndex) => itemIndex !== index))}
                  >
                    Remove
                  </Button>
                </Stack>
              </Paper>
            ))}
            <Stack direction="row" spacing={1}>
              <Button onClick={() => setCriteria((items) => [...items, cloneCriterion()])} variant="outlined">
                Add criterion
              </Button>
              <Button type="submit" variant="contained">{existing ? 'Save changes' : 'Create'}</Button>
              <Button onClick={() => navigate(`/recruiter/jobs/${jobId}`)}>Back to job</Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
