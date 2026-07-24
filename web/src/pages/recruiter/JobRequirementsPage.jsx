import { useEffect, useState } from 'react';
import { Box, Button, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useNavigate, useParams } from 'react-router-dom';
import { configureJobRequirements, getJob } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';
import {
  applyImportance,
  cloneRequirement,
  hydrateRequirement,
  importanceOptions,
  prepareRequirementsForApi,
} from './requirementScoring.js';

export default function JobRequirementsPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [requirements, setRequirements] = useState([cloneRequirement()]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [requirementsLocked, setRequirementsLocked] = useState(false);

  useEffect(() => {
    getJob(jobId)
      .then((job) => {
        setRequirementsLocked(Boolean(job.requirements_locked_at) || job.status !== 'draft');
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
        normalize_weights: true,
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
        {requirementsLocked ? (
          <Alert severity="info" sx={{ mb: 2 }}>
            Requirements are locked because this job has been posted, ensuring consistent AI resume screening.
          </Alert>
        ) : null}
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
                    disabled={requirementsLocked}
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
                    disabled={requirementsLocked}
                    value={req.description}
                    onChange={(event) => update(index, 'description', event.target.value)}
                  />
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                    <TextField
                      label="Importance"
                      select
                      disabled={requirementsLocked}
                      value={req.importance_level}
                      onChange={(event) => update(index, 'importance_level', event.target.value)}
                    >
                      {importanceOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label} — {option.description}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Stack>
                  <Button
                    color="error"
                    disabled={requirementsLocked || requirements.length === 1}
                    onClick={() => setRequirements((items) => items.filter((_, itemIndex) => itemIndex !== index))}
                  >
                    Remove
                  </Button>
                </Stack>
              </Paper>
            ))}
            <Stack direction="row" spacing={1}>
              <Button disabled={requirementsLocked} onClick={() => setRequirements((items) => [...items, cloneRequirement()])} variant="outlined">
                Add requirement
              </Button>
              <Button disabled={requirementsLocked} type="submit" variant="contained">Save requirements</Button>
              <Button onClick={() => navigate(`/recruiter/jobs/${jobId}`)}>Back to job</Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
