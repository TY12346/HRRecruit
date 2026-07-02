import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import {
  configureJobRequirements,
  createJob,
  createJobEvaluationForm,
  getJob,
  updateJob,
} from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';
import {
  applyCriterionImportance,
  cloneCriterion,
  criterionImportanceOptions,
  prepareCriteriaForApi,
} from './evaluationScoring.js';
import {
  applyImportance,
  cloneRequirement,
  importanceOptions,
  prepareRequirementsForApi,
} from './requirementScoring.js';

const blankJob = {
  title: '',
  description: '',
  employment_type: 'full_time',
  approximate_salary: '',
  location: '',
  status: 'draft',
};
const employmentTypeOptions = [
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
  { value: 'temporary', label: 'Temporary' },
];

const createSteps = ['Job details', 'Requirements', 'Evaluation form'];

export default function JobCreateEditPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(jobId);
  const [form, setForm] = useState(blankJob);
  const [activeStep, setActiveStep] = useState(0);
  const [requirements, setRequirements] = useState([cloneRequirement()]);
  const [evaluationTitle, setEvaluationTitle] = useState('Interview Evaluation Form');
  const [criteria, setCriteria] = useState([cloneCriterion()]);
  const [createdJobId, setCreatedJobId] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(isEdit);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!isEdit) {
      return undefined;
    }

    let active = true;
    getJob(jobId)
      .then((job) => {
        if (!active) {
          return;
        }
        setForm({
          title: job.title ?? '',
          description: job.description ?? '',
          employment_type: job.employment_type ?? '',
          approximate_salary: job.approximate_salary ?? '',
          location: job.location ?? '',
          status: job.status ?? 'draft',
        });
      })
      .catch((err) => active && setError(getApiErrorMessage(err, 'Unable to load job.')))
      .finally(() => active && setIsLoading(false));

    return () => {
      active = false;
    };
  }, [isEdit, jobId]);

  const setField = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const updateRequirement = (index, field, value) => {
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

  const updateCriterion = (index, field, value) => {
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

  const handleEditSubmit = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    setError('');

    try {
      const saved = await updateJob(jobId, form);
      navigate(`/recruiter/jobs/${saved.id}`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to save job.'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateStepSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (activeStep < createSteps.length - 1) {
      setActiveStep((step) => step + 1);
      return;
    }

    setIsSaving(true);
    try {
      let job;
      try {
        job = createdJobId ? await updateJob(createdJobId, form) : await createJob(form);
        setCreatedJobId(job.id);
      } catch (err) {
        setActiveStep(0);
        throw err;
      }

      try {
        await configureJobRequirements(job.id, {
          requirements: prepareRequirementsForApi(requirements),
          normalize_weights: true,
        });
      } catch (err) {
        setActiveStep(1);
        throw err;
      }

      await createJobEvaluationForm(job.id, {
        title: evaluationTitle,
        criteria: prepareCriteriaForApi(criteria),
      });
      navigate(`/recruiter/jobs/${job.id}`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to create job. Please review the highlighted step and try again.'));
    } finally {
      setIsSaving(false);
    }
  };

  const renderJobDetails = () => (
    <Stack spacing={2}>
      <TextField label="Job title" required value={form.title} onChange={setField('title')} />
      <TextField label="Description" required multiline minRows={5} value={form.description} onChange={setField('description')} />
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        <TextField label="Employment type" required select value={form.employment_type} onChange={setField('employment_type')}>
          {employmentTypeOptions.map((option) => (
            <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
          ))}
        </TextField>
        <TextField label="Approximate salary" required type="number" value={form.approximate_salary} onChange={setField('approximate_salary')} />
        <TextField label="Location" required value={form.location} onChange={setField('location')} />
        <FormControl>
          <InputLabel>Status</InputLabel>
          <Select label="Status" value={form.status} onChange={setField('status')}>
            <MenuItem value="draft">Draft</MenuItem>
            <MenuItem value="open">Open</MenuItem>
            <MenuItem value="closed">Closed</MenuItem>
          </Select>
        </FormControl>
      </Stack>
    </Stack>
  );

  const renderRequirements = () => (
    <Stack spacing={2}>
      {requirements.map((requirement, index) => (
        <Paper key={index} variant="outlined" sx={{ p: 2 }}>
          <Stack spacing={2}>
            <TextField
              label="Type"
              select
              value={requirement.requirement_type}
              onChange={(event) => updateRequirement(index, 'requirement_type', event.target.value)}
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
              value={requirement.description}
              onChange={(event) => updateRequirement(index, 'description', event.target.value)}
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Importance"
                select
                helperText="Choose recruiter-friendly priority instead of entering a raw numeric weight."
                value={requirement.importance_level}
                onChange={(event) => updateRequirement(index, 'importance_level', event.target.value)}
              >
                {importanceOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label} — {option.description}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>
            <Typography variant="caption" color="text.secondary">
              HRRecruit converts this priority into an AI scoring weight: {requirement.weight_score}.
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
      <Button onClick={() => setRequirements((items) => [...items, cloneRequirement()])} variant="outlined">
        Add requirement
      </Button>
    </Stack>
  );

  const renderEvaluationForm = () => (
    <Stack spacing={2}>
      <TextField label="Form title" required value={evaluationTitle} onChange={(event) => setEvaluationTitle(event.target.value)} />
      {criteria.map((criterion, index) => (
        <Paper key={index} variant="outlined" sx={{ p: 2 }}>
          <Stack spacing={2}>
            <TextField
              label="Criterion name"
              required
              value={criterion.criterion_name}
              onChange={(event) => updateCriterion(index, 'criterion_name', event.target.value)}
            />
            <TextField
              label="Description"
              required
              value={criterion.description}
              onChange={(event) => updateCriterion(index, 'description', event.target.value)}
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Max score"
                type="number"
                value={criterion.max_score}
                onChange={(event) => updateCriterion(index, 'max_score', event.target.value)}
              />
              <TextField
                label="Interview scoring importance"
                select
                helperText="Choose how much this competency should influence the interviewer score."
                value={criterion.importance_level}
                onChange={(event) => updateCriterion(index, 'importance_level', event.target.value)}
              >
                {criterionImportanceOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label} — {option.description}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>
            <Typography variant="caption" color="text.secondary">
              HRRecruit stores this as evaluation weight {criterion.weight_score} for weighted interview scoring.
            </Typography>
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
      <Button onClick={() => setCriteria((items) => [...items, cloneCriterion()])} variant="outlined">
        Add criterion
      </Button>
    </Stack>
  );

  const renderCreateStep = () => {
    if (activeStep === 0) {
      return renderJobDetails();
    }
    if (activeStep === 1) {
      return renderRequirements();
    }
    return renderEvaluationForm();
  };

  if (isEdit) {
    return (
      <Box>
        <RecruiterNav />
        <Paper component="form" onSubmit={handleEditSubmit} sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>Edit job</Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>Update job posting details.</Typography>
          {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
          {isLoading ? (
            <CircularProgress />
          ) : (
            <Stack spacing={2}>
              {renderJobDetails()}
              <Stack direction="row" spacing={1}>
                <Button disabled={isSaving} type="submit" variant="contained">{isSaving ? 'Saving…' : 'Save job'}</Button>
                <Button onClick={() => navigate(-1)} variant="outlined">Cancel</Button>
              </Stack>
            </Stack>
          )}
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      <RecruiterNav />
      <Paper component="form" onSubmit={handleCreateStepSubmit} sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>Create job</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Fill in the job details, then configure requirements, then configure the evaluation form before creating the job.
        </Typography>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {createSteps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        <Stack spacing={2}>
          {renderCreateStep()}
          <Stack direction="row" spacing={1}>
            <Button disabled={activeStep === 0 || isSaving} onClick={() => setActiveStep((step) => step - 1)} variant="outlined">
              Back
            </Button>
            <Button disabled={isSaving} type="submit" variant="contained">
              {isSaving ? 'Creating…' : activeStep === createSteps.length - 1 ? 'Create job' : 'Next'}
            </Button>
            <Button disabled={isSaving} onClick={() => navigate(-1)} variant="text">Cancel</Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
}
