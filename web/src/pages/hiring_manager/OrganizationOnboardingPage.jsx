import { useState } from 'react';
import { Box, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useNavigate } from 'react-router-dom';
import { createOrganization } from '../../api/client.js';
import { getApiErrorMessage } from './hiringManagerUtils.js';

const emptyForm = { name: '', registration_no: '', email: '', contact_number: '', address: '' };

export default function OrganizationOnboardingPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState(emptyForm);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await createOrganization(formData);
      navigate('/hiring-manager/onboarding/subscription', { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Unable to create organization profile.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Paper sx={{ p: 3, width: '100%' }}>
      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <Typography component="h1" variant="h5">Create organization</Typography>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <TextField label="Organization name" name="name" onChange={(event) => setFormData((current) => ({ ...current, name: event.target.value }))} required value={formData.name} />
          <TextField label="Registration number" name="registration_no" onChange={(event) => setFormData((current) => ({ ...current, registration_no: event.target.value }))} required value={formData.registration_no} />
          <TextField label="Organization email" name="email" onChange={(event) => setFormData((current) => ({ ...current, email: event.target.value }))} required type="email" value={formData.email} />
          <TextField label="Contact number" name="contact_number" onChange={(event) => setFormData((current) => ({ ...current, contact_number: event.target.value }))} required value={formData.contact_number} />
          <TextField label="Address" minRows={4} multiline name="address" onChange={(event) => setFormData((current) => ({ ...current, address: event.target.value }))} required value={formData.address} />
          <Button disabled={isSubmitting} type="submit" variant="contained">{isSubmitting ? 'Creating…' : 'Create organization'}</Button>
        </Stack>
      </Box>
    </Paper>
  );
}
