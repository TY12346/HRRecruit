import { useEffect, useState } from 'react';
import {

  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import {
  completeDemoPayment,
  createBillingCheckoutSession,
  getBillingInvoices,
  getBillingPlans,
  getSubscriptionUsage,
  getCurrentSubscription,
  reactivateSubscription,
  subscribeToPlan,
  upgradeSubscription,
} from '../../api/client.js';
import HiringManagerNav from './HiringManagerNav.jsx';
import { formatCurrency, formatDateTime, getApiErrorMessage, titleize } from './hiringManagerUtils.js';

export default function BillingPage() {
  const [plans, setPlans] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [capacity, setCapacity] = useState(null);
  const [isAutoRenew, setIsAutoRenew] = useState(false);
  const [pendingSubscription, setPendingSubscription] = useState(null);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [isSubscriptionActionLoading, setIsSubscriptionActionLoading] = useState(false);

  const loadBilling = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [plansData, subscriptionResult, invoiceData, usageData] = await Promise.all([
        getBillingPlans(),
        getCurrentSubscription().catch((subscriptionError) => {
          if (subscriptionError.response?.status === 404) {
            return null;
          }
          throw subscriptionError;
        }),
        getBillingInvoices(),
        getSubscriptionUsage().catch(() => null),
      ]);
      setPlans(plansData);
      setSubscription(subscriptionResult);
      setInvoices(invoiceData);
      setCapacity(usageData);
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
        const [plansData, subscriptionResult, invoiceData, usageData] = await Promise.all([
          getBillingPlans(),
          getCurrentSubscription().catch((subscriptionError) => {
            if (subscriptionError.response?.status === 404) {
              return null;
            }
            throw subscriptionError;
          }),
          getBillingInvoices(),
          getSubscriptionUsage().catch(() => null),
        ]);
        if (isMounted) {
          setPlans(plansData);
          setSubscription(subscriptionResult);
          setInvoices(invoiceData);
          setCapacity(usageData);
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

  const handleStripeCheckout = async () => {
    if (!pendingSubscription) return;
    setError('');
    try {
      const checkout = await createBillingCheckoutSession({ subscriptionId: pendingSubscription.id });
      window.location.assign(checkout.checkout_url);
    } catch (checkoutError) {
      setError(getApiErrorMessage(checkoutError, 'Unable to start Stripe sandbox checkout.'));
    }
  };

  return (
    <Box>
      <HiringManagerNav />
      <Stack spacing={3}>
        <Box>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
            {subscription ? 'Billing' : 'Select your subscription plan'}
          </Typography>
          <Typography color="text.secondary">
            {subscription
              ? 'Manage your subscription and complete the built-in demo payment flow when needed.'
              : 'Choose a subscription plan to finish setting up your hiring manager workspace.'}
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
                  ) : null}
                </Stack>
              ) : (
                <Typography color="text.secondary">No active subscription found.</Typography>
              )}
            </Stack>
          </CardContent>
        </Card>

        {pendingSubscription ? (
          <Alert
            action={<Stack direction="row" spacing={1}><Button color="inherit" onClick={handleStripeCheckout}>Pay with Stripe sandbox</Button><Button color="inherit" onClick={handleCompletePayment}>Demo payment</Button></Stack>}
            severity="info"
          >
            Pending payment for {pendingSubscription.plan?.name}. Continue to Stripe Checkout in test mode, or use the local demo fallback.
          </Alert>
        ) : null}

        <FormControlLabel
          control={<Checkbox checked={isAutoRenew} onChange={(event) => setIsAutoRenew(event.target.checked)} />}
          label="Enable auto-renew for selected plan"
        />

        {capacity ? (
          <Card><CardContent><Typography variant="h6" sx={{ mb: 2 }}>Current capacity usage</Typography>
            <Grid container spacing={2}>{Object.entries(capacity.usage).map(([key, item]) => {
              const percent = item.limit ? (item.used / item.limit) * 100 : 0;
              return <Grid item xs={12} sm={6} lg={3} key={key}><Stack spacing={0.5}>
                <Typography sx={{ fontWeight: 600 }}>{titleize(key)}</Typography>
                <Typography>{item.used} / {item.limit} used</Typography>
                <Typography color={percent >= 100 ? 'error' : percent >= 80 ? 'warning.main' : 'text.secondary'}>
                  {item.remaining} remaining{percent >= 100 ? '. Limit reached; deactivate an account or close an open job before adding another.' : ''}
                </Typography>
              </Stack></Grid>;
            })}</Grid>
          </CardContent></Card>
        ) : null}

        <Grid container spacing={2}>
          {plans.map((plan) => (
            <Grid item xs={12} sm={6} lg={3} key={plan.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Stack spacing={1.5}>
                    <Typography component="h3" variant="h6">{plan.name}</Typography>
                    <Typography component="p" variant="h4" sx={{ fontWeight: 700 }}>
                      {formatCurrency(plan.price)}
                    </Typography>
                    <Typography color="text.secondary">{titleize(plan.billing_cycle)} billing</Typography>
                    <Typography>{plan.max_hiring_managers} Hiring Manager{plan.max_hiring_managers === 1 ? '' : 's'}</Typography>
                    <Typography>{plan.max_recruiters} Recruiter{plan.max_recruiters === 1 ? '' : 's'}</Typography>
                    <Typography>{plan.max_interviewers} Interviewer{plan.max_interviewers === 1 ? '' : 's'}</Typography>
                    <Typography>{plan.max_active_job_postings} active job postings</Typography>
                    <Typography color="text.secondary">All HRRecruit features included. Plans differ only by organization capacity.</Typography>
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
