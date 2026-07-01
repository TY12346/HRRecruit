import { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { completeGoogleCalendarOAuth } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';

const submittedOAuthCodes = new Set();

export default function GoogleCalendarCallbackPage() {
  const location = useLocation();
  const hasSubmittedOAuthCode = useRef(false);
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('Connecting Google Calendar…');

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const state = params.get('state');
    if (!code || !state) {
      setStatus('error');
      setMessage('Google did not return the required authorization code and state. Please try connecting again.');
      return;
    }
    if (hasSubmittedOAuthCode.current || submittedOAuthCodes.has(code)) {
      setStatus('info');
      setMessage('This Google Calendar authorization response is already being processed. If the calendar does not show as connected, start the connection again from HRRecruit.');
      return;
    }
    hasSubmittedOAuthCode.current = true;
    submittedOAuthCodes.add(code);
    completeGoogleCalendarOAuth({ code, state })
      .then((result) => {
        setStatus('success');
        setMessage(`Google Calendar connected${result.connected_email ? ` as ${result.connected_email}` : ''}. Future scheduled interviews can sync to Calendar.`);
      })
      .catch((err) => {
        setStatus('error');
        setMessage(getApiErrorMessage(err, 'Unable to complete Google Calendar connection.'));
      });
  }, [location.search]);

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>Google Calendar connection</Typography>
          {status === 'loading' ? <CircularProgress /> : null}
          <Alert severity={status === 'success' ? 'success' : status === 'error' ? 'error' : 'info'}>{message}</Alert>
          <Stack direction="row" spacing={1}>
            <Button component={RouterLink} to="/recruiter/interviews" variant="contained">View interviews</Button>
            <Button component={RouterLink} to="/recruiter/applications" variant="outlined">Back to applications</Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
}
