import { useState } from 'react';
import {

  Box,
  Button,
  Link as MuiLink,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import { login } from '../../api/client.js';
import { useAuthStore } from '../../store/authStore.js';
import { getDashboardPathForRole } from '../../routes/guards.jsx';

function getErrorMessage(error) {
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.join(' ');
  }
  if (typeof detail === 'string') {
    return detail;
  }
  return 'Unable to log in. Check your email and password, then try again.';
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((state) => state.setSession);
  const sessionMessage = useAuthStore((state) => state.sessionMessage);
  const clearSessionMessage = useAuthStore((state) => state.clearSessionMessage);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    clearSessionMessage();
    setIsSubmitting(true);

    try {
      const data = await login(formData);
      setSession({
        accessToken: data.tokens.access,
        refreshToken: data.tokens.refresh,
        user: data.user,
      });

      const redirectPath = location.state?.from?.pathname ?? getDashboardPathForRole(data.user.role);
      navigate(redirectPath, { replace: true });
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 520, mx: 'auto' }}>
      <Typography component="h2" variant="h5" sx={{ mb: 1 }}>
        Staff Login
      </Typography>

      {error || sessionMessage ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || sessionMessage}
        </Alert>
      ) : null}

      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
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
            autoComplete="current-password"
            label="Password"
            name="password"
            onChange={handleChange}
            required
            type="password"
            value={formData.password}
          />
          <Button disabled={isSubmitting} type="submit" variant="contained">
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </Button>
          <MuiLink component={RouterLink} to="/forgot-password" sx={{ alignSelf: 'flex-start' }}>
            Forgot password?
          </MuiLink>
        </Stack>
      </Box>

      <Typography color="text.secondary" sx={{ mt: 3 }}>
        For companies new to HRRecruit, start by {' '}
        <MuiLink component={RouterLink} to="/register">
          registering a hiring manager account
        </MuiLink>
        .
      </Typography>
    </Paper>
  );
}
