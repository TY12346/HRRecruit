import { useEffect, useState } from 'react';
import { Alert, Box, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import { getProfile, updateProfile } from '../../api/client.js';
import { useAuthStore } from '../../store/authStore.js';

function buildProfileForm(user) {
  return {
    full_name: user?.full_name ?? '',
    phone_number: user?.phone_number ?? '',
    linkedin_url: user?.linkedin_url ?? '',
    personal_summary: user?.personal_summary ?? '',
  };
}

function collectProfileErrors(error) {
  const data = error.response?.data;
  if (!data || typeof data !== 'object') {
    return 'Unable to update your profile. Please try again.';
  }

  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
    .join(' ');
}

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);
  const [formData, setFormData] = useState(buildProfileForm(user));
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadProfile = async () => {
      setIsLoading(true);
      setError('');

      try {
        const profile = await getProfile();
        if (isMounted) {
          updateUser(profile);
          setFormData(buildProfileForm(profile));
        }
      } catch {
        if (isMounted) {
          setError('Unable to load your profile right now.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadProfile();

    return () => {
      isMounted = false;
    };
  }, [updateUser]);

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');
    setIsSubmitting(true);

    try {
      const data = await updateProfile(formData);
      updateUser(data.user);
      setFormData(buildProfileForm(data.user));
      setSuccessMessage(data.message ?? 'Profile updated successfully.');
    } catch (submitError) {
      setError(collectProfileErrors(submitError));
    } finally {
      setIsSubmitting(false);
    }
  };

  const isApplicant = user?.role === 'applicant';

  return (
    <Paper sx={{ p: 3 }}>
      <Typography component="h2" variant="h5" sx={{ mb: 1 }}>
        My Profile
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        View your HRRecruit account details and update editable profile fields.
      </Typography>

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}
      {successMessage ? (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      ) : null}

      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <TextField disabled label="Email address" value={user?.email ?? ''} />
          <TextField disabled label="Role" value={user?.role ?? ''} />
          <TextField
            disabled={isLoading}
            label="Full name"
            name="full_name"
            onChange={handleChange}
            required
            value={formData.full_name}
          />
          <TextField
            disabled={isLoading}
            label="Phone number"
            name="phone_number"
            onChange={handleChange}
            value={formData.phone_number}
          />
          {isApplicant ? (
            <>
              <TextField
                disabled={isLoading}
                label="LinkedIn URL"
                name="linkedin_url"
                onChange={handleChange}
                type="url"
                value={formData.linkedin_url}
              />
              <TextField
                disabled={isLoading}
                label="Personal summary"
                minRows={4}
                multiline
                name="personal_summary"
                onChange={handleChange}
                value={formData.personal_summary}
              />
              <Alert severity="info">
                Resume upload is handled by the backend API and will be connected to the UI in a later task.
              </Alert>
            </>
          ) : null}
          <Button disabled={isLoading || isSubmitting} type="submit" variant="contained">
            {isSubmitting ? 'Saving…' : 'Save profile'}
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
}
