import { useEffect, useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { configureJobRequirements, getJob } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';
import {
  applyImportance,
  applyMatchThreshold,
  cloneRequirement,
  hydrateRequirement,
  importanceOptions,
  matchThresholdOptions,
  prepareRequirementsForApi,
} from './requirementScoring.js';

export default function JobRequirementsPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [requirements, setRequirements] = useState([cloneRequirement()]);
  const [normalize, setNormalize] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    getJob(jobId)
      .then((job) => {
        if (job.requirements?.length) {
          setRequirements(job.requirements.map(hydrateRequirement));
        }
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load requirements.')));
  }, [jobId]);

  const update = (index, field, value) => {
    setRequirements((items) => items.map((item, itemIndex) => {
      if (itemIndex !== index) {
        return item;
      }
      if (field === 'importance_level') {
        return applyImportance(item, value);
      }
      if (field === 'match_strictness') {
        return applyMatchThreshold(item, value);
      }
      return { ...item, [field]: value };
    }));
  };

  const save = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    try {
      await configureJobRequirements(jobId, {
        requirements: prepareRequirementsForApi(requirements),
        normalize_weights: normalize,
      });
      setSuccess('Requirements saved.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to save requirements.'));
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Job requirements</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Configure requirements using recruiter-friendly priority and match strictness labels. HRRecruit still stores the numeric values needed by AI screening behind the scenes.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        <Box component="form" onSubmit={save}>
          <Stack spacing={2}>
            {requirements.map((req, index) => (
              <Paper key={index} variant="outlined" sx={{ p: 2 }}>
                <Stack spacing={2}>
                  <TextField
                    label="Type"
                    select
                    value={req.requirement_type}
                    onChange={(event) => update(index, 'requirement_type', event.target.value)}
                  >
                    <MenuItem value="skill">Skill</MenuItem>
                    <MenuItem value="experience">Experience</MenuItem>
                    <MenuItem value="education">Education</MenuItem>
                    <MenuItem value="certification">Certification</MenuItem>
                    <MenuItem value="other">Other</MenuItem>
                  </TextField>
                  <TextField
                    label="Description"
                    required
                    value={req.description}
                    onChange={(event) => update(index, 'description', event.target.value)}
                  />
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                    <TextField
                      label="Importance"
                      select
                      helperText="Choose priority instead of a raw numeric weight."
                      value={req.importance_level}
                      onChange={(event) => update(index, 'importance_level', event.target.value)}
                    >
                      {importanceOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label} — {option.description}
                        </MenuItem>
                      ))}
                    </TextField>
                    <TextField
                      label="Minimum match required"
                      select
                      helperText="Choose how strong the resume evidence must be."
                      value={req.match_strictness}
                      onChange={(event) => update(index, 'match_strictness', event.target.value)}
                    >
                      {matchThresholdOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label} — {option.description}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Stack>
                  <Typography variant="caption" color="text.secondary">
                    AI scoring values: weight {req.weight_score}, minimum threshold {req.minimum_threshold}.
                  </Typography>
                  <Button
                    color="error"
                    disabled={requirements.length === 1}
                    onClick={() => setRequirements((items) => items.filter((_, itemIndex) => itemIndex !== index))}
                  >
                    Remove
                  </Button>
                </Stack>
              </Paper>
            ))}
            <FormControlLabel
              control={<Checkbox checked={normalize} onChange={(event) => setNormalize(event.target.checked)} />}
              label="Auto-balance importance values so the AI scoring weights add up correctly"
            />
            <Typography variant="caption" color="text.secondary">
              This mirrors real recruitment systems: recruiters choose business priorities, while the system normalizes the underlying scoring weights.
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button onClick={() => setRequirements((items) => [...items, cloneRequirement()])} variant="outlined">
                Add requirement
              </Button>
              <Button type="submit" variant="contained">Save requirements</Button>
              <Button onClick={() => navigate(`/recruiter/jobs/${jobId}`)}>Back to job</Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
