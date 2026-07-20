import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, CircularProgress, Grid, Paper, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { completeDemoPayment, getBillingPlans, subscribeToPlan } from '../../api/client.js';
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

  const handleSelectPlan = async (planId) => {
    setSelectedPlanId(planId);
    setError('');
    try {
      const response = await subscribeToPlan({ planId });
      await completeDemoPayment({
        subscriptionId: response.subscription.id,
        transactionReference: `DEMO-ONBOARDING-${Date.now()}`,
      });
      navigate('/hiring-manager', { replace: true });
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
            <Grid item xs={12} md={4} key={plan.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Stack spacing={1.5}>
                    <Typography component="h2" variant="h6">{plan.name}</Typography>
                    <Typography component="p" variant="h4" sx={{ fontWeight: 700 }}>{formatCurrency(plan.price)}</Typography>
                    <Typography color="text.secondary">{titleize(plan.billing_cycle)} billing</Typography>
                    <Typography>Maximum open job postings: {plan.max_job_postings}</Typography>
                    <Typography color="text.secondary">{plan.features_description}</Typography>
                    <Box><Button disabled={selectedPlanId !== null} onClick={() => handleSelectPlan(plan.id)} variant="contained">{selectedPlanId === plan.id ? 'Processing payment…' : 'Select plan and pay'}</Button></Box>
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
