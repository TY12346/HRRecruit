import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { approveHiringDecision, getPendingHiringDecisions, rejectHiringDecision } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './hrHeadUtils.js';
import ApplicationFlowSummary from '../../components/ApplicationFlowSummary.jsx';
import { getApplicationStatusInfo } from '../../utils/recruitmentFlow.js';

export default function PendingHiringDecisionsPage() {
  const [decisions, setDecisions] = useState([]);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [reviewAction, setReviewAction] = useState('approve');
  const [justification, setJustification] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadDecisions = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getPendingHiringDecisions();
      setDecisions(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, 'Unable to load pending hiring decisions.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadInitialDecisions = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getPendingHiringDecisions();
        if (isMounted) {
          setDecisions(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, 'Unable to load pending hiring decisions.'));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadInitialDecisions();

    return () => {
      isMounted = false;
    };
  }, []);

  const openReviewDialog = (decision, action) => {
    setSelectedDecision(decision);
    setReviewAction(action);
    setJustification('');
  };

  const closeReviewDialog = () => {
    if (!isSubmitting) {
      setSelectedDecision(null);
    }
  };

  const submitReview = async () => {
    if (!justification.trim()) {
      setError('A HR head justification is required.');
      return;
    }

    setError('');
    setSuccessMessage('');
    setIsSubmitting(true);
    try {
      if (reviewAction === 'approve') {
        await approveHiringDecision(selectedDecision.id, justification);
      } else {
        await rejectHiringDecision(selectedDecision.id, justification);
      }
      setSuccessMessage(`Hiring decision ${reviewAction === 'approve' ? 'approved' : 'rejected'} successfully.`);
      setSelectedDecision(null);
      await loadDecisions();
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Unable to review hiring decision.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box>
      <HRHeadNav />
      <Stack spacing={3}>
        <Box>
          <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
            Pending Hiring Decisions
          </Typography>
          <Typography color="text.secondary">
            Review recruiter hiring or rejection recommendations and provide HR approval justification.
          </Typography>
        </Box>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading pending decisions" /> : null}

        {!isLoading && decisions.length === 0 ? <Alert severity="info">No pending hiring decisions.</Alert> : null}

        {decisions.map((decision) => {
          const application = decision.application ?? {};
          const applicant = application.applicant ?? {};
          return (
            <Card key={decision.id}>
              <CardContent>
                <Stack spacing={2}>
                  <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
                    <Box>
                      <Typography component="h3" variant="h6">
                        {titleize(decision.decision)} recommendation for {applicant.full_name ?? 'Applicant'}
                      </Typography>
                      <Typography color="text.secondary">
                        {application.job_title ?? 'Job'} • Submitted by {decision.recruiter_name} on {formatDateTime(decision.submitted_at)}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1}>
                      <Button color="success" onClick={() => openReviewDialog(decision, 'approve')} variant="contained">
                        Approve
                      </Button>
                      <Button color="error" onClick={() => openReviewDialog(decision, 'reject')} variant="outlined">
                        Reject
                      </Button>
                    </Stack>
                  </Stack>
                  <Typography><strong>Recruiter justification:</strong> {decision.recruiter_justification}</Typography>
                  <Typography><strong>Applicant:</strong> {applicant.email ?? '—'} {applicant.phone_number ? `• ${applicant.phone_number}` : ''}</Typography>
                  <Typography><strong>Application status:</strong> {getApplicationStatusInfo(application.status, 'hr_head').label}</Typography>
                  <ApplicationFlowSummary status={application.status} role="hr_head" compact />
                  <Typography><strong>AI final score:</strong> {application.final_score ?? '—'}</Typography>
                </Stack>
              </CardContent>
            </Card>
          );
        })}
      </Stack>

      <Dialog fullWidth maxWidth="sm" open={Boolean(selectedDecision)} onClose={closeReviewDialog}>
        <DialogTitle>{reviewAction === 'approve' ? 'Approve hiring decision' : 'Reject hiring decision'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="HR justification"
            minRows={4}
            multiline
            onChange={(event) => setJustification(event.target.value)}
            required
            sx={{ mt: 1 }}
            value={justification}
          />
        </DialogContent>
        <DialogActions>
          <Button disabled={isSubmitting} onClick={closeReviewDialog}>Cancel</Button>
          <Button disabled={isSubmitting} onClick={submitReview} variant="contained">
            {isSubmitting ? 'Submitting…' : reviewAction === 'approve' ? 'Approve' : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
