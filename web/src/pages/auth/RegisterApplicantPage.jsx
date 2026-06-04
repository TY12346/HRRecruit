import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Link as MuiLink,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { registerApplicant } from '../../api/client.js';
import { useAuthStore } from '../../store/authStore.js';

function collectApiErrors(error) {
  const data = error.response?.data;
  if (!data || typeof data !== 'object') {
    return 'Unable to register. Please check the form and try again.';
  }

  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
    .join(' ');
}

export default function RegisterApplicantPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phoneNumber: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const data = await registerApplicant(formData);
      setSession({
        accessToken: data.tokens.access,
        refreshToken: data.tokens.refresh,
        user: data.user,
      });
      navigate('/profile', { replace: true });
    } catch (submitError) {
      setError(collectApiErrors(submitError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 560, mx: 'auto' }}>
      <Typography component="h2" variant="h5" sx={{ mb: 1 }}>
        Applicant Registration
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Create a job applicant account. Staff accounts are created by HR department heads.
      </Typography>

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <TextField
            autoComplete="name"
            label="Full name"
            name="fullName"
            onChange={handleChange}
            required
            value={formData.fullName}
          />
          <TextField
            autoComplete="email"
            label="Email address"
            name="email"
            onChange={handleChange}
            required
            type="email"
            value={formData.email}
          />
          <TextField
            autoComplete="tel"
            label="Phone number"
            name="phoneNumber"
            onChange={handleChange}
            value={formData.phoneNumber}
          />
          <TextField
            autoComplete="new-password"
            helperText="Use at least 8 characters."
            label="Password"
            name="password"
            onChange={handleChange}
            required
            type="password"
            value={formData.password}
          />
          <Button disabled={isSubmitting} type="submit" variant="contained">
            {isSubmitting ? 'Creating account…' : 'Create applicant account'}
          </Button>
        </Stack>
      </Box>

      <Typography color="text.secondary" sx={{ mt: 3 }}>
        Already have an account?{' '}
        <MuiLink component={RouterLink} to="/login">
          Sign in
        </MuiLink>
        .
      </Typography>
    </Paper>
  );
}
