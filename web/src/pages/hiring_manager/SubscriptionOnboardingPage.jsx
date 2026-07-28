import { useEffect, useState } from 'react';
import { Button, Card, CardContent, CircularProgress, Grid, Paper, Stack, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useNavigate } from 'react-router-dom';
import { completeDemoPayment, createBillingCheckoutSession, getBillingPlans, subscribeToPlan } from '../../api/client.js';
import { formatCurrency, getApiErrorMessage, titleize } from './hiringManagerUtils.js';

export default function SubscriptionOnboardingPage() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPlanId, setSelectedPlanId] = useState(null);

  useEffect(() => {
    getBillingPlans()
      .then(setPlans)
      .catch((loadError) => setError(getApiErrorMessage(loadError, 'Unable to load subscription plans.')))
      .finally(() => setIsLoading(false));
  }, []);

  const handleSelectPlan = async (planId, gateway) => {
    setSelectedPlanId(planId);
    setError('');
    try {
      const response = await subscribeToPlan({ planId });
      if (gateway === 'stripe') {
        const checkout = await createBillingCheckoutSession({ subscriptionId: response.subscription.id });
        window.location.assign(checkout.checkout_url);
      } else {
        await completeDemoPayment({
          subscriptionId: response.subscription.id,
          transactionReference: `DEMO-ONBOARDING-${Date.now()}`,
        });
        navigate('/hiring-manager', { replace: true });
      }
    } catch (selectError) {
      setError(getApiErrorMessage(selectError, 'Unable to select subscription plan.'));
    } finally {
      setSelectedPlanId(null);
    }
  };

  return (
    <Paper sx={{ p: 3, width: '100%' }}>
      <Stack spacing={3}>
        <Typography component="h1" variant="h5">Select your subscription plan</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading subscription plans" /> : null}
        <Grid container spacing={2}>
          {plans.map((plan) => (
            <Grid item xs={12} sm={6} lg={3} key={plan.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Stack spacing={1.5}>
                    <Typography component="h2" variant="h6">{plan.name}</Typography>
                    <Typography component="p" variant="h4" sx={{ fontWeight: 700 }}>{formatCurrency(plan.price)}</Typography>
                    <Typography color="text.secondary">{titleize(plan.billing_cycle)} billing</Typography>
                    <Typography>{plan.max_hiring_managers} Hiring Manager{plan.max_hiring_managers === 1 ? '' : 's'}</Typography>
                    <Typography>{plan.max_recruiters} Recruiter{plan.max_recruiters === 1 ? '' : 's'}</Typography>
                    <Typography>{plan.max_interviewers} Interviewer{plan.max_interviewers === 1 ? '' : 's'}</Typography>
                    <Typography>{plan.max_active_job_postings} active job postings</Typography>
                    <Typography color="text.secondary">All HRRecruit features included. Plans differ only by organization capacity.</Typography>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                      <Button disabled={selectedPlanId !== null} onClick={() => handleSelectPlan(plan.id, 'stripe')} variant="contained">{selectedPlanId === plan.id ? 'Starting checkout…' : 'Pay with Stripe sandbox'}</Button>
                      <Button disabled={selectedPlanId !== null} onClick={() => handleSelectPlan(plan.id, 'demo')} variant="outlined">Demo payment</Button>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Stack>
    </Paper>
  );
}
