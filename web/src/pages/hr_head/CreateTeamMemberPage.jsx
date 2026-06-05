import { useState } from 'react';
import { Alert, Box, Button, FormControl, InputLabel, MenuItem, Paper, Select, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { createOrganizationMember } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { getApiErrorMessage } from './hrHeadUtils.js';

const emptyForm = {
  full_name: '',
  email: '',
  phone_number: '',
  role: 'recruiter',
};

export default function CreateTeamMemberPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState(emptyForm);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
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
      setFormData(emptyForm);
      setTimeout(() => navigate('/hr-head/team'), 800);
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Unable to create team member.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box>
      <HRHeadNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
          Create Team Member
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Create recruiter or interviewer accounts for your organization. The backend emails temporary credentials through the configured email backend.
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {successMessage ? <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert> : null}

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField label="Full name" name="full_name" onChange={handleChange} required value={formData.full_name} />
            <TextField label="Email address" name="email" onChange={handleChange} required type="email" value={formData.email} />
            <TextField label="Phone number" name="phone_number" onChange={handleChange} value={formData.phone_number} />
            <FormControl fullWidth>
              <InputLabel id="member-role-label">Role</InputLabel>
              <Select label="Role" labelId="member-role-label" name="role" onChange={handleChange} value={formData.role}>
                <MenuItem value="recruiter">Recruiter</MenuItem>
                <MenuItem value="interviewer">Interviewer</MenuItem>
              </Select>
            </FormControl>
            <Stack direction="row" spacing={1}>
              <Button disabled={isSubmitting} type="submit" variant="contained">
                {isSubmitting ? 'Creating…' : 'Create member'}
              </Button>
              <Button component={RouterLink} to="/hr-head/team" variant="outlined">
                Back to team
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
