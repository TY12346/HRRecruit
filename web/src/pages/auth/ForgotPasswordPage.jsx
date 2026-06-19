import { useState } from 'react';
import { Alert, Box, Button, Link as MuiLink, Paper, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { requestPasswordReset } from '../../api/client.js';

function getErrorMessage(error) {
  const data = error.response?.data;
  if (!data || typeof data !== 'object') return 'Unable to send reset link. Please try again.';
  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
    .join(' ');
}

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [developmentResetLink, setDevelopmentResetLink] = useState('');
  const [emailDeliveryNote, setEmailDeliveryNote] = useState('');

  const submitRequest = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setDevelopmentResetLink('');
    setEmailDeliveryNote('');
    setIsSubmitting(true);
    try {
      const data = await requestPasswordReset({ email });
      setSuccess(data.message ?? 'If the email exists, a password reset link has been sent.');
      setDevelopmentResetLink(data.reset_link ?? '');
      setEmailDeliveryNote(data.email_delivery_note ?? '');
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 560, mx: 'auto' }}>
      <Typography component="h2" variant="h5" sx={{ mb: 1 }}>
        Forgot password
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Enter your account email. HRRecruit will send a secure reset link that opens a separate reset password page.
      </Typography>
      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
      {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
      {developmentResetLink ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          {emailDeliveryNote || 'Development email mode detected. Configure SMTP or SendGrid to deliver reset emails to an inbox; use this reset link to continue locally.'}{' '}
          <MuiLink href={developmentResetLink}>
            Open reset password page
          </MuiLink>
        </Alert>
      ) : null}

      <Box component="form" onSubmit={submitRequest}>
        <Stack spacing={2}>
          <TextField autoComplete="email" label="Email address" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
          <Button disabled={isSubmitting} type="submit" variant="contained">{isSubmitting ? 'Sending…' : 'Submit'}</Button>
        </Stack>
      </Box>

      <Typography color="text.secondary" sx={{ mt: 3 }}>
        Remember your password? <MuiLink component={RouterLink} to="/login">Back to login</MuiLink>.
      </Typography>
    </Paper>
  );
}
