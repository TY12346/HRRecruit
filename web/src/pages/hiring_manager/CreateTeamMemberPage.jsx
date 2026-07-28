import { useState } from 'react';
import { Box, Button, FormControl, InputLabel, MenuItem, Paper, Select, Stack, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink } from 'react-router-dom';
import { createOrganizationMember } from '../../api/client.js';
import HiringManagerNav from './HiringManagerNav.jsx';
import { getApiErrorMessage } from './hiringManagerUtils.js';

const emptyForm = {
  full_name: '',
  email: '',
  phone_number: '',
  role: 'recruiter',
};

export default function CreateTeamMemberPage() {
  const [formData, setFormData] = useState(emptyForm);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [deliveryMode, setDeliveryMode] = useState('email');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');
    setIsSubmitting(true);

    try {
      const response = await createOrganizationMember(formData);
      setSuccessMessage(response.message ?? 'Team member created successfully. Temporary credentials were sent by email.');
      setDeliveryMode(response.email_delivery ?? 'email');
      setFormData(emptyForm);
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Unable to create team member.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box>
      <HiringManagerNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
          Create Team Member
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Create hiring manager, recruiter, or interviewer accounts for your organization.
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {successMessage ? <Alert severity={deliveryMode === 'email' ? 'success' : 'warning'} sx={{ mb: 2 }}>{successMessage}</Alert> : null}

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField label="Full name" name="full_name" onChange={handleChange} required value={formData.full_name} />
            <TextField label="Email address" name="email" onChange={handleChange} required type="email" value={formData.email} />
            <TextField label="Phone number" name="phone_number" onChange={handleChange} value={formData.phone_number} />
            <FormControl fullWidth>
              <InputLabel id="member-role-label">Role</InputLabel>
              <Select label="Role" labelId="member-role-label" name="role" onChange={handleChange} value={formData.role}>
                <MenuItem value="hr_head">Hiring Manager</MenuItem>
                <MenuItem value="recruiter">Recruiter</MenuItem>
                <MenuItem value="interviewer">Interviewer</MenuItem>
              </Select>
            </FormControl>
            <Stack direction="row" spacing={1}>
              <Button disabled={isSubmitting} type="submit" variant="contained">
                {isSubmitting ? 'Creating…' : 'Create member'}
              </Button>
              <Button component={RouterLink} to="/hiring-manager/team" variant="outlined">
                Back to team
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
