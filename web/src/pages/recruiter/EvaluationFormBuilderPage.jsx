import { useEffect, useState } from 'react';
import { Alert, Box, Button, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { createJobEvaluationForm, getJob } from '../../api/client.js';
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
  const [title, setTitle] = useState('Interview Evaluation Form');
  const [criteria, setCriteria] = useState([cloneCriterion()]);
  const [existing, setExisting] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    getJob(jobId)
      .then((job) => {
        if (job.interview_evaluation_form) {
          setExisting(job.interview_evaluation_form);
          setTitle(job.interview_evaluation_form.title);
          setCriteria((job.interview_evaluation_form.criteria ?? []).map(hydrateCriterion));
        }
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load evaluation form.')));
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
      const saved = await createJobEvaluationForm(jobId, { title, criteria: payloadCriteria });
      setSuccess('Evaluation form created.');
      setExisting(saved);
      setCriteria((saved.criteria ?? payloadCriteria).map(hydrateCriterion));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to create evaluation form.'));
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Evaluation form builder</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Define interviewer scoring criteria using real-world competency importance labels. Existing forms are displayed read-only because the current backend supports creation once.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        <Box component="form" onSubmit={save}>
          <Stack spacing={2}>
            <TextField disabled={Boolean(existing)} label="Form title" value={title} onChange={(event) => setTitle(event.target.value)} />
            {criteria.map((criterion, index) => (
              <Paper key={index} variant="outlined" sx={{ p: 2 }}>
                <Stack spacing={2}>
                  <TextField
                    disabled={Boolean(existing)}
                    label="Criterion name"
                    required
                    value={criterion.criterion_name}
                    onChange={(event) => update(index, 'criterion_name', event.target.value)}
                  />
                  <TextField
                    disabled={Boolean(existing)}
                    label="Description"
                    required
                    value={criterion.description}
                    onChange={(event) => update(index, 'description', event.target.value)}
                  />
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                    <TextField
                      disabled={Boolean(existing)}
                      label="Max score"
                      type="number"
                      value={criterion.max_score}
                      onChange={(event) => update(index, 'max_score', event.target.value)}
                    />
                    <TextField
                      disabled={Boolean(existing)}
                      label="Interview scoring importance"
                      select
                      helperText="Choose how much this competency should influence the interviewer score."
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
                  <Typography variant="caption" color="text.secondary">
                    Interview scoring value: weight {criterion.weight_score}.
                  </Typography>
                  {!existing ? (
                    <Button
                      color="error"
                      disabled={criteria.length === 1}
                      onClick={() => setCriteria((items) => items.filter((_, itemIndex) => itemIndex !== index))}
                    >
                      Remove
                    </Button>
                  ) : null}
                </Stack>
              </Paper>
            ))}
            <Stack direction="row" spacing={1}>
              {!existing ? (
                <Button onClick={() => setCriteria((items) => [...items, cloneCriterion()])} variant="outlined">
                  Add criterion
                </Button>
              ) : null}
              {!existing ? <Button type="submit" variant="contained">Create form</Button> : null}
              <Button onClick={() => navigate(`/recruiter/jobs/${jobId}`)}>Back to job</Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
