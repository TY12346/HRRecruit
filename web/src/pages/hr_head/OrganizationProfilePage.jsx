import { useEffect, useState } from 'react';
import { Alert, Box, Button, CircularProgress, Paper, Stack, TextField, Typography } from '@mui/material';
import { createOrganization, getOrganization, updateOrganization } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { getApiErrorMessage } from './hrHeadUtils.js';

const emptyForm = {
  name: '',
  registration_no: '',
  email: '',
  contact_number: '',
  address: '',
};

function buildForm(organization) {
  return {
    name: organization?.name ?? '',
    registration_no: organization?.registration_no ?? '',
    email: organization?.email ?? '',
    contact_number: organization?.contact_number ?? '',
    address: organization?.address ?? '',
  };
}

export default function OrganizationProfilePage() {
  const [organization, setOrganization] = useState(null);
  const [formData, setFormData] = useState(emptyForm);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadOrganization = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getOrganization();
        if (isMounted) {
          setOrganization(data);
          setFormData(buildForm(data));
        }
      } catch (loadError) {
        if (isMounted && loadError.response?.status !== 404) {
          setError(getApiErrorMessage(loadError, 'Unable to load organization profile.'));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadOrganization();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');
    setIsSubmitting(true);

    try {
      const response = organization ? await updateOrganization(formData) : await createOrganization(formData);
      const savedOrganization = response.organization ?? response;
      setOrganization(savedOrganization);
      setFormData(buildForm(savedOrganization));
      setSuccessMessage(response.message ?? 'Organization profile saved successfully.');
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Unable to save organization profile.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box>
      <HRHeadNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
          Organization Profile
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Create or update the organization account managed by this HR head.
        </Typography>

        {isLoading ? <CircularProgress aria-label="Loading organization" sx={{ mb: 2 }} /> : null}
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {successMessage ? <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert> : null}

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField disabled={isLoading} label="Organization name" name="name" onChange={handleChange} required value={formData.name} />
            <TextField disabled={isLoading} label="Registration number" name="registration_no" onChange={handleChange} required value={formData.registration_no} />
            <TextField disabled={isLoading} label="Organization email" name="email" onChange={handleChange} required type="email" value={formData.email} />
            <TextField disabled={isLoading} label="Contact number" name="contact_number" onChange={handleChange} required value={formData.contact_number} />
            <TextField disabled={isLoading} label="Address" minRows={4} multiline name="address" onChange={handleChange} required value={formData.address} />
            <Button disabled={isLoading || isSubmitting} type="submit" variant="contained">
              {isSubmitting ? 'Saving…' : organization ? 'Update organization' : 'Create organization'}
            </Button>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
