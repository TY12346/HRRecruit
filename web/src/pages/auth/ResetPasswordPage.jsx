import { useState } from 'react';
import { Alert, Box, Button, Link as MuiLink, Paper, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { confirmPasswordReset } from '../../api/client.js';

function getErrorMessage(error) {
  const data = error.response?.data;
  if (!data || typeof data !== 'object') return 'Unable to reset password. Please try again.';
  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
    .join(' ');
}

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const [email] = useState(searchParams.get('email') ?? '');
  const [resetToken] = useState(searchParams.get('token') ?? '');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(!email || !resetToken ? 'This reset link is invalid or incomplete. Please request a new password reset link.' : '');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitConfirm = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    if (newPassword !== confirmPassword) {
      setError('New password and confirmation do not match.');
      return;
    }
    setIsSubmitting(true);
    try {
      const data = await confirmPasswordReset({ email, resetToken, newPassword });
      setSuccess(data.message ?? 'Password reset successful. You can now sign in.');
      setNewPassword('');
      setConfirmPassword('');
    } catch (confirmError) {
      setError(getErrorMessage(confirmError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 560, mx: 'auto' }}>
      <Typography component="h2" variant="h5" sx={{ mb: 1 }}>
        Reset password
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Enter a new password for {email || 'your HRRecruit account'}.
      </Typography>
      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
      {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}

      <Box component="form" onSubmit={submitConfirm}>
        <Stack spacing={2}>
          <TextField disabled label="Email address" value={email} />
          <TextField autoComplete="new-password" disabled={!email || !resetToken || Boolean(success)} label="New password" onChange={(event) => setNewPassword(event.target.value)} required type="password" value={newPassword} />
          <TextField autoComplete="new-password" disabled={!email || !resetToken || Boolean(success)} label="Confirm new password" onChange={(event) => setConfirmPassword(event.target.value)} required type="password" value={confirmPassword} />
          <Button disabled={isSubmitting || !email || !resetToken || Boolean(success)} type="submit" variant="contained">{isSubmitting ? 'Resetting…' : 'Reset password'}</Button>
          <Button component={RouterLink} to="/forgot-password" type="button">Request a new reset link</Button>
        </Stack>
      </Box>

      <Typography color="text.secondary" sx={{ mt: 3 }}>
        Remember your password? <MuiLink component={RouterLink} to="/login">Back to login</MuiLink>.
      </Typography>
    </Paper>
  );
}
