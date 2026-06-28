import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import {
  cancelSubscription,
  completeDemoPayment,
  getBillingInvoices,
  getBillingPlans,
  getCurrentSubscription,
  reactivateSubscription,
  subscribeToPlan,
  upgradeSubscription,
} from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { formatCurrency, formatDateTime, getApiErrorMessage, titleize } from './hrHeadUtils.js';

export default function BillingPage() {
  const [plans, setPlans] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [isAutoRenew, setIsAutoRenew] = useState(false);
  const [pendingSubscription, setPendingSubscription] = useState(null);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [isSubscriptionActionLoading, setIsSubscriptionActionLoading] = useState(false);

  const loadBilling = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [plansData, subscriptionResult, invoiceData] = await Promise.all([
        getBillingPlans(),
        getCurrentSubscription().catch((subscriptionError) => {
          if (subscriptionError.response?.status === 404) {
            return null;
          }
          throw subscriptionError;
        }),
        getBillingInvoices(),
      ]);
      setPlans(plansData);
      setSubscription(subscriptionResult);
      setInvoices(invoiceData);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, 'Unable to load billing details.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const loadInitialBilling = async () => {
      setIsLoading(true);
      setError('');
      try {
        const [plansData, subscriptionResult, invoiceData] = await Promise.all([
          getBillingPlans(),
          getCurrentSubscription().catch((subscriptionError) => {
            if (subscriptionError.response?.status === 404) {
              return null;
            }
            throw subscriptionError;
          }),
          getBillingInvoices(),
        ]);
        if (isMounted) {
          setPlans(plansData);
          setSubscription(subscriptionResult);
          setInvoices(invoiceData);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, 'Unable to load billing details.'));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadInitialBilling();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSelectPlan = async (plan) => {
    setSelectedPlanId(plan.id);
    setError('');
    setSuccessMessage('');
    try {
      const request = subscription ? upgradeSubscription : subscribeToPlan;
      const response = await request({ planId: plan.id, isAutoRenew });
      setPendingSubscription(response.subscription);
      setSuccessMessage(response.message ?? 'Plan selected. Complete demo payment to activate it.');
    } catch (selectError) {
      setError(getApiErrorMessage(selectError, 'Unable to select subscription plan.'));
    } finally {
      setSelectedPlanId(null);
    }
  };

  const handleCancelSubscription = async () => {
    setIsSubscriptionActionLoading(true);
    setError('');
    setSuccessMessage('');
    try {
      const response = await cancelSubscription({ reason: cancelReason });
      setSubscription(response.subscription);
      setCancelReason('');
      setSuccessMessage(response.message ?? 'Subscription cancellation scheduled.');
    } catch (cancelError) {
      setError(getApiErrorMessage(cancelError, 'Unable to schedule subscription cancellation.'));
    } finally {
      setIsSubscriptionActionLoading(false);
    }
  };

  const handleReactivateSubscription = async () => {
    setIsSubscriptionActionLoading(true);
    setError('');
    setSuccessMessage('');
    try {
      const response = await reactivateSubscription();
      setSubscription(response.subscription);
      setSuccessMessage(response.message ?? 'Subscription resumed successfully.');
    } catch (reactivateError) {
      setError(getApiErrorMessage(reactivateError, 'Unable to resume subscription.'));
    } finally {
      setIsSubscriptionActionLoading(false);
    }
  };

  const handleCompletePayment = async () => {
    if (!pendingSubscription) {
      return;
    }
    setError('');
    setSuccessMessage('');
    try {
      const response = await completeDemoPayment({
        subscriptionId: pendingSubscription.id,
        transactionReference: `DEMO-${Date.now()}`,
      });
      setSubscription(response.subscription);
      setPendingSubscription(null);
      setSuccessMessage(response.message ?? 'Demo payment completed successfully.');
      await loadBilling();
    } catch (paymentError) {
      setError(getApiErrorMessage(paymentError, 'Unable to complete demo payment.'));
    }
  };

  return (
    <Box>
      <HRHeadNav />
      <Stack spacing={3}>
        <Box>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
            Billing
          </Typography>
          <Typography color="text.secondary">
            Select a subscription plan and complete the built-in demo payment flow.
          </Typography>
        </Box>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading billing" /> : null}

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Typography component="h3" variant="h6">Current subscription</Typography>
              {subscription ? (
                <Stack spacing={1.5}>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" alignItems="center">
                    <Typography sx={{ fontWeight: 700 }}>
                      {subscription.plan?.name} • {titleize(subscription.status)}
                    </Typography>
                    <Chip
                      color={subscription.cancel_at_period_end ? 'warning' : 'success'}
                      label={subscription.cancel_at_period_end ? 'Cancels at period end' : 'Active renewal'}
                      size="small"
                    />
                    <Chip
                      label={subscription.is_auto_renew ? 'Auto-renew on' : 'Auto-renew off'}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>
                  <Typography color="text.secondary">
                    Current period: {formatDateTime(subscription.start_date)} – {formatDateTime(subscription.end_date)}
                  </Typography>
                  {subscription.cancel_at_period_end ? (
                    <Alert
                      action={(
                        <Button
                          color="inherit"
                          disabled={isSubscriptionActionLoading}
                          onClick={handleReactivateSubscription}
                        >
                          Resume
                        </Button>
                      )}
                      severity="warning"
                    >
                      This subscription remains usable until {formatDateTime(subscription.end_date)}.
                      {subscription.cancellation_reason ? ` Reason: ${subscription.cancellation_reason}` : ''}
                    </Alert>
                  ) : (
                    <Stack spacing={1} sx={{ maxWidth: 560 }}>
                      <Typography color="text.secondary">
                        Real billing systems usually schedule cancellation for the end of the paid period instead of
                        cutting access immediately.
                      </Typography>
                      <TextField
                        label="Cancellation reason (optional)"
                        onChange={(event) => setCancelReason(event.target.value)}
                        size="small"
                        value={cancelReason}
                      />
                      <Box>
                        <Button
                          color="warning"
                          disabled={isSubscriptionActionLoading}
                          onClick={handleCancelSubscription}
                          variant="outlined"
                        >
                          Cancel at period end
                        </Button>
                      </Box>
                    </Stack>
                  )}
                </Stack>
              ) : (
                <Typography color="text.secondary">No active subscription found.</Typography>
              )}
            </Stack>
          </CardContent>
        </Card>

        {pendingSubscription ? (
          <Alert
            action={<Button color="inherit" onClick={handleCompletePayment}>Complete demo payment</Button>}
            severity="info"
          >
            Pending payment for {pendingSubscription.plan?.name}. Use the demo payment button to activate it.
          </Alert>
        ) : null}

        <FormControlLabel
          control={<Checkbox checked={isAutoRenew} onChange={(event) => setIsAutoRenew(event.target.checked)} />}
          label="Enable auto-renew for selected plan"
        />

        <Grid container spacing={2}>
          {plans.map((plan) => (
            <Grid item xs={12} md={4} key={plan.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Stack spacing={1.5}>
                    <Typography component="h3" variant="h6">{plan.name}</Typography>
                    <Typography component="p" variant="h4" sx={{ fontWeight: 700 }}>
                      {formatCurrency(plan.price)}
                    </Typography>
                    <Typography color="text.secondary">{titleize(plan.billing_cycle)} billing</Typography>
                    <Typography>Maximum open job postings: {plan.max_job_postings}</Typography>
                    <Typography color="text.secondary">{plan.features_description}</Typography>
                    <Button disabled={selectedPlanId === plan.id} onClick={() => handleSelectPlan(plan)} variant="contained">
                      {selectedPlanId === plan.id ? 'Selecting…' : subscription ? 'Change plan' : 'Select plan'}
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Card>
          <CardContent>
            <Typography component="h3" variant="h6" sx={{ mb: 2 }}>Invoices and payments</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Invoice</TableCell>
                  <TableCell>Plan</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Due</TableCell>
                  <TableCell>Paid at</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {invoices.map((invoice) => (
                  <TableRow key={invoice.id}>
                    <TableCell>{invoice.invoice_number}</TableCell>
                    <TableCell>{invoice.plan_name}</TableCell>
                    <TableCell>{formatCurrency(invoice.amount, invoice.currency)}</TableCell>
                    <TableCell>{titleize(invoice.status)}</TableCell>
                    <TableCell>{titleize(invoice.billing_reason)}</TableCell>
                    <TableCell>{formatDateTime(invoice.due_at)}</TableCell>
                    <TableCell>{formatDateTime(invoice.paid_at)}</TableCell>
                  </TableRow>
                ))}
                {!invoices.length ? (
                  <TableRow><TableCell colSpan={7}>No invoices yet.</TableCell></TableRow>
                ) : null}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
