import { useEffect, useState } from 'react';
import {

  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useNavigate, useParams } from 'react-router-dom';
import { createJobRequisition, getJob, updateJob } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';

const employmentTypeOptions = [
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
  { value: 'temporary', label: 'Temporary' },
];

const departmentOptions = [
  { value: 'Engineering', label: 'Engineering' },
  { value: 'Product', label: 'Product' },
  { value: 'Sales', label: 'Sales' },
  { value: 'Marketing', label: 'Marketing' },
  { value: 'Customer Support', label: 'Customer Support' },
  { value: 'Finance', label: 'Finance' },
  { value: 'Human Resources', label: 'Human Resources' },
  { value: 'Operations', label: 'Operations' },
  { value: 'Legal', label: 'Legal' },
  { value: 'Other', label: 'Other / custom department' },
];

const blankJob = {
  title: '',
  description: '',
  employment_type: 'full_time',
  approximate_salary: '',
  salary_range: '',
  location: '',
  core_responsibilities: '',
  requirements_qualifications: '',
  department: 'Engineering',
  custom_department: '',
  target_start_date: '',
  benefits_perks: '',
  position_status: 'new_headcount',
  reason_for_hire: '',
  impact_of_not_hiring: '',
  vacancies: 1,
  application_deadline: '',
  status: 'draft',
};

export default function JobCreateEditPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(jobId);
  const [form, setForm] = useState(blankJob);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(isEdit);
  const [isSaving, setIsSaving] = useState(false);
  const [showPostConfirmation, setShowPostConfirmation] = useState(false);
  const [initialStatus, setInitialStatus] = useState('draft');

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
          employment_type: job.employment_type ?? 'full_time',
          approximate_salary: job.approximate_salary ?? '',
          salary_range: job.salary_range ?? '',
          location: job.location ?? '',
          core_responsibilities: job.core_responsibilities ?? '',
          requirements_qualifications: job.requirements_qualifications ?? '',
          department: job.department ?? 'Engineering',
          custom_department: job.custom_department ?? '',
          target_start_date: job.target_start_date ?? '',
          benefits_perks: job.benefits_perks ?? '',
          position_status: job.position_status ?? 'new_headcount',
          reason_for_hire: job.reason_for_hire ?? '',
          impact_of_not_hiring: job.impact_of_not_hiring ?? '',
          vacancies: job.vacancies ?? 1,
          application_deadline: job.application_deadline ?? '',
          status: job.status ?? 'draft',
        });
        setInitialStatus(job.status ?? 'draft');
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

  const getPayload = () => ({
    ...form,
    custom_department: form.department === 'Other' ? form.custom_department : '',
  });

  const saveJob = async () => {
    setIsSaving(true);
    setError('');

    try {
      if (isEdit) {
        const saved = await updateJob(jobId, getPayload());
        navigate(`/recruiter/jobs/${saved.id}`);
      } else {
        await createJobRequisition(getPayload());
        navigate('/recruiter/job-requisitions');
      }
    } catch (err) {
      setError(getApiErrorMessage(err, isEdit ? 'Unable to save job.' : 'Unable to submit job requisition.'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (isEdit && initialStatus === 'draft' && form.status === 'open') {
      setShowPostConfirmation(true);
      return;
    }
    saveJob();
  };

  const confirmPost = () => {
    setShowPostConfirmation(false);
    saveJob();
  };

  const renderDetails = () => (
    <Stack spacing={2}>
      <TextField label="Job title" required value={form.title} onChange={setField('title')} />
      <TextField label="Job summary" required multiline minRows={3} value={form.description} onChange={setField('description')} />
      <TextField
        label="Core responsibilities"
        required
        multiline
        minRows={4}
        value={form.core_responsibilities}
        onChange={setField('core_responsibilities')}
      />
      <TextField
        label="Requirements & qualifications"
        required
        multiline
        minRows={4}
        value={form.requirements_qualifications}
        onChange={setField('requirements_qualifications')}
      />
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        <TextField label="Employment type" required select value={form.employment_type} onChange={setField('employment_type')}>
          {employmentTypeOptions.map((option) => (
            <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
          ))}
        </TextField>
        <TextField label="Location" required value={form.location} onChange={setField('location')} />
      </Stack>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        <TextField label="Department" required select value={form.department} onChange={setField('department')}>
          {departmentOptions.map((option) => (
            <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
          ))}
        </TextField>
        {form.department === 'Other' ? (
          <TextField label="Custom department name" required value={form.custom_department} onChange={setField('custom_department')} />
        ) : null}
        <TextField
          label="Target start date"
          InputLabelProps={{ shrink: true }}
          type="date"
          value={form.target_start_date}
          onChange={setField('target_start_date')}
        />
      </Stack>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        <TextField label="Salary range" required placeholder="e.g. RM 5,000 - RM 7,000" value={form.salary_range} onChange={setField('salary_range')} />
        <FormControl required>
          <InputLabel>Position status</InputLabel>
          <Select label="Position status" value={form.position_status} onChange={setField('position_status')}>
            <MenuItem value="new_headcount">New headcount / expansion</MenuItem>
            <MenuItem value="backfill">Backfill / replacement</MenuItem>
          </Select>
        </FormControl>
      </Stack>
      <TextField
        label="Benefits & perks"
        multiline
        minRows={3}
        value={form.benefits_perks}
        onChange={setField('benefits_perks')}
      />
      <TextField
        label="Reason for hire"
        required
        multiline
        minRows={3}
        value={form.reason_for_hire}
        onChange={setField('reason_for_hire')}
      />
      <TextField
        label="Impact of not hiring"
        required
        multiline
        minRows={3}
        value={form.impact_of_not_hiring}
        onChange={setField('impact_of_not_hiring')}
      />
      {isEdit ? (
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField label="Approximate salary" type="number" value={form.approximate_salary} onChange={setField('approximate_salary')} />
          <TextField label="Number of vacancies" type="number" inputProps={{ min: 1 }} value={form.vacancies} onChange={setField('vacancies')} />
          <TextField label="Application deadline" type="date" InputLabelProps={{ shrink: true }} value={form.application_deadline} onChange={setField('application_deadline')} />
          <FormControl>
            <InputLabel>Status</InputLabel>
            <Select label="Status" value={form.status} onChange={setField('status')}>
              <MenuItem value="draft">Draft</MenuItem>
              <MenuItem value="open">Open</MenuItem>
              <MenuItem value="application_intake_closed">Application Intake Closed</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      ) : null}
    </Stack>
  );

  return (
    <Box>
      <RecruiterNav />
      <Paper component="form" onSubmit={handleSubmit} sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>{isEdit ? 'Edit job' : 'Create job requisition'}</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          {isEdit
            ? 'Update job posting details.'
            : ''}
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? (
          <CircularProgress />
        ) : (
          <Stack spacing={2}>
            {renderDetails()}
            <Stack direction="row" spacing={1}>
              <Button disabled={isSaving} type="submit" variant="contained">
                {isSaving ? (isEdit ? 'Saving…' : 'Submitting…') : (isEdit ? 'Save job' : 'Submit requisition')}
              </Button>
              <Button disabled={isSaving} onClick={() => navigate(-1)} variant="text">Cancel</Button>
            </Stack>
          </Stack>
        )}
      </Paper>
      <Dialog open={showPostConfirmation} onClose={() => !isSaving && setShowPostConfirmation(false)}>
        <DialogTitle>Confirm to post this job?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            To ensure consistency of AI resume screening, the job requirements cannot be changed once this job is posted.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button disabled={isSaving} onClick={() => setShowPostConfirmation(false)}>Cancel</Button>
          <Button autoFocus disabled={isSaving} onClick={confirmPost} variant="contained">
            Confirm and post
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
