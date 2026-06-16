import { useEffect, useState } from 'react';
import { Alert, Box, Button, Link as MuiLink, Paper, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { confirmPasswordReset, requestPasswordReset } from '../../api/client.js';

function getErrorMessage(error) {
  const data = error.response?.data;
  if (!data || typeof data !== 'object') return 'Unable to reset password. Please try again.';
  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
    .join(' ');
}

export default function ForgotPasswordPage() {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get('email') ?? '');
  const [otpCode, setOtpCode] = useState(searchParams.get('otp') ?? '');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [step, setStep] = useState(searchParams.get('email') && searchParams.get('otp') ? 'confirm' : 'request');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (searchParams.get('email') && searchParams.get('otp')) {
      setSuccess('Reset link opened. Enter a new password to finish resetting your account.');
    }
  }, [searchParams]);

  const submitRequest = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setIsSubmitting(true);
    try {
      const data = await requestPasswordReset({ email });
      setSuccess(data.message ?? 'If the email exists, reset instructions were sent.');
      setStep('confirm');
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  };

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
      const data = await confirmPasswordReset({ email, otpCode, newPassword });
      setSuccess(data.message ?? 'Password reset successful. You can now sign in.');
      setOtpCode('');
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
        Forgot password
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Enter your account email. HRRecruit will send a one-time reset code using the configured email backend.
      </Typography>
      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
      {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}

      {step === 'request' ? (
        <Box component="form" onSubmit={submitRequest}>
          <Stack spacing={2}>
            <TextField autoComplete="email" label="Email address" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
            <Button disabled={isSubmitting} type="submit" variant="contained">{isSubmitting ? 'Sending…' : 'Send reset code'}</Button>
          </Stack>
        </Box>
      ) : (
        <Box component="form" onSubmit={submitConfirm}>
          <Stack spacing={2}>
            <TextField disabled label="Email address" value={email} />
            <TextField inputProps={{ maxLength: 6 }} label="Reset code" onChange={(event) => setOtpCode(event.target.value)} required value={otpCode} />
            <TextField autoComplete="new-password" label="New password" onChange={(event) => setNewPassword(event.target.value)} required type="password" value={newPassword} />
            <TextField autoComplete="new-password" label="Confirm new password" onChange={(event) => setConfirmPassword(event.target.value)} required type="password" value={confirmPassword} />
            <Button disabled={isSubmitting} type="submit" variant="contained">{isSubmitting ? 'Resetting…' : 'Reset password'}</Button>
            <Button disabled={isSubmitting} onClick={() => setStep('request')} type="button">Use a different email</Button>
          </Stack>
        </Box>
      )}

      <Typography color="text.secondary" sx={{ mt: 3 }}>
        Remember your password? <MuiLink component={RouterLink} to="/login">Back to login</MuiLink>.
      </Typography>
    </Paper>
  );
}
