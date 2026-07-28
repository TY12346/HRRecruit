import { useEffect, useState } from 'react';
import { Button, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom';
import Alert from '../../components/TimedAlert.jsx';
import { getHiringManagerOnboardingStatus } from '../../api/client.js';

export default function SubscriptionPaymentReturnPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [error, setError] = useState('');
  const cancelled = params.get('checkout') === 'cancelled';

  useEffect(() => {
    if (cancelled) return undefined;
    let active = true;
    let attempts = 0;
    const checkActivation = async () => {
      try {
        const status = await getHiringManagerOnboardingStatus();
        if (!active) return;
        if (status.subscription_selected) {
          navigate('/hiring-manager/billing?checkout=success', { replace: true });
          return;
        }
        attempts += 1;
        if (attempts < 10) window.setTimeout(checkActivation, 1500);
        else setError('Stripe accepted the checkout, but subscription activation is still pending. Verify the webhook configuration, then refresh this page.');
      } catch {
        if (active) setError('Unable to verify subscription activation. Please refresh and try again.');
      }
    };
    checkActivation();
    return () => { active = false; };
  }, [cancelled, navigate]);

  return <Paper sx={{ p: 3, maxWidth: 680, mx: 'auto' }}><Stack spacing={2} alignItems="flex-start">
    <Typography component="h1" variant="h5">Stripe sandbox checkout</Typography>
    {cancelled ? <Alert severity="warning">Checkout was cancelled. No payment was recorded and your existing subscription was not changed.</Alert> : null}
    {!cancelled && !error ? <><CircularProgress /><Typography>Payment received. Waiting for the verified Stripe webhook to activate your subscription…</Typography></> : null}
    {error ? <Alert severity="error">{error}</Alert> : null}
    <Button component={RouterLink} to="/hiring-manager/onboarding/subscription" variant="outlined">Back to plans</Button>
  </Stack></Paper>;
}
