import { useEffect, useState } from 'react';
import {

  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useNavigate } from 'react-router-dom';
import {
  createOrganization,
  deleteOrganization,
  getOrganization,
  requestOrganizationDeletionOtp,
  updateOrganization,
} from '../../api/client.js';
import HiringManagerNav from './HiringManagerNav.jsx';
import { getApiErrorMessage } from './hiringManagerUtils.js';

const emptyForm = {
  name: '',
  registration_no: '',
  email: '',
  contact_number: '',
  address: '',
};

function buildForm(organization) {
  return {
    name: organization?.name ?? '',
    registration_no: organization?.registration_no ?? '',
    email: organization?.email ?? '',
    contact_number: organization?.contact_number ?? '',
    address: organization?.address ?? '',
  };
}

export default function OrganizationProfilePage() {
  const navigate = useNavigate();
  const [organization, setOrganization] = useState(null);
  const [formData, setFormData] = useState(emptyForm);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteStep, setDeleteStep] = useState(1);
  const [deletionOtp, setDeletionOtp] = useState('');
  const [deleteDialogError, setDeleteDialogError] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadOrganization = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getOrganization();
        if (isMounted) {
          setOrganization(data);
          setFormData(buildForm(data));
        }
      } catch (loadError) {
        if (isMounted && loadError.response?.status !== 404) {
          setError(getApiErrorMessage(loadError, 'Unable to load organization profile.'));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadOrganization();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const closeDeleteDialog = () => {
    if (isDeleting) {
      return;
    }
    setIsDeleteDialogOpen(false);
    setDeleteStep(1);
    setDeletionOtp('');
    setDeleteDialogError('');
  };

  const handleSendDeletionOtp = async () => {
    setIsDeleting(true);
    setDeleteDialogError('');
    try {
      await requestOrganizationDeletionOtp();
      setDeleteStep(2);
    } catch (requestError) {
      setDeleteDialogError(getApiErrorMessage(requestError, 'Unable to send the deletion OTP.'));
    } finally {
      setIsDeleting(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccessMessage('');
    setIsSubmitting(true);

    try {
      const response = organization ? await updateOrganization(formData) : await createOrganization(formData);
      const savedOrganization = response.organization ?? response;
      setOrganization(savedOrganization);
      setFormData(buildForm(savedOrganization));
      setSuccessMessage(response.message ?? 'Organization profile saved successfully.');
      if (!organization) {
        navigate('/hiring-manager/billing', { replace: true });
      }
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Unable to save organization profile.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteOrganization = async () => {
    setError('');
    setSuccessMessage('');
    setIsDeleting(true);

    try {
      const response = await deleteOrganization(deletionOtp);
      setOrganization(null);
      setFormData(emptyForm);
      setSuccessMessage(response.message ?? 'Organization account deleted successfully.');
      setIsDeleteDialogOpen(false);
      setDeleteStep(1);
      setDeletionOtp('');
    } catch (deleteError) {
      setDeleteDialogError(getApiErrorMessage(deleteError, 'Unable to delete organization account.'));
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Box>
      <HiringManagerNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
          Organization Profile
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Create or update the organization account managed by this hiring manager.
        </Typography>

        {isLoading ? <CircularProgress aria-label="Loading organization" sx={{ mb: 2 }} /> : null}
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {successMessage ? <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert> : null}

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField disabled={isLoading} label="Organization name" name="name" onChange={handleChange} required value={formData.name} />
            <TextField disabled={isLoading} label="Registration number" name="registration_no" onChange={handleChange} required value={formData.registration_no} />
            <TextField disabled={isLoading} label="Organization email" name="email" onChange={handleChange} required type="email" value={formData.email} />
            <TextField disabled={isLoading} label="Contact number" name="contact_number" onChange={handleChange} required value={formData.contact_number} />
            <TextField disabled={isLoading} label="Address" minRows={4} multiline name="address" onChange={handleChange} required value={formData.address} />
            <Button disabled={isLoading || isSubmitting} type="submit" variant="contained">
              {isSubmitting ? 'Saving…' : organization ? 'Update organization' : 'Create organization'}
            </Button>
          </Stack>
        </Box>
      </Paper>

      {organization ? (
        <Paper sx={{ p: 3, mt: 3, border: '1px solid', borderColor: 'error.light' }}>
          <Typography component="h3" variant="h6" color="error" sx={{ fontWeight: 700, mb: 1 }}>
            Delete organization account
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            This soft-deletes the organization account, deactivates its memberships, and disables recruiter and interviewer team accounts.
          </Typography>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Deletion is only allowed after draft/open jobs are closed, active applications are resolved, interviews are completed or cancelled, pending hiring decisions and offers are cleared, and active billing items are resolved.
          </Alert>
          <Button color="error" disabled={isLoading || isSubmitting || isDeleting} onClick={() => setIsDeleteDialogOpen(true)} variant="outlined">
            Delete organization account
          </Button>
        </Paper>
      ) : null}

      <Dialog fullWidth maxWidth="sm" onClose={closeDeleteDialog} open={isDeleteDialogOpen}>
        <DialogTitle>
          {deleteStep === 1 ? 'Delete organization account?' : deleteStep === 2 ? 'Enter deletion OTP' : 'Final confirmation'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {deleteDialogError ? <Alert severity="error">{deleteDialogError}</Alert> : null}
            {deleteStep === 1 ? <>
              <Alert severity="warning">
                Are you sure you want to begin deleting {organization?.name}? Team members will lose access to this workspace.
              </Alert>
              <Box>
                <Typography sx={{ fontWeight: 700, mb: 1 }}>Before deletion is permitted, make sure:</Typography>
                <List dense sx={{ listStyleType: 'disc', pl: 3 }}>
                  <ListItem sx={{ display: 'list-item', p: 0 }}>Draft and open job postings are closed.</ListItem>
                  <ListItem sx={{ display: 'list-item', p: 0 }}>Active applications, interviews, hiring decisions, and sent offers are resolved.</ListItem>
                  <ListItem sx={{ display: 'list-item', p: 0 }}>Active subscriptions and pending payments are resolved.</ListItem>
                </List>
              </Box>
            </> : null}
            {deleteStep === 2 ? <>
              <Alert severity="info">A 6-digit OTP has been sent to your hiring manager email address. It expires in 10 minutes.</Alert>
              <TextField
                autoFocus
                disabled={isDeleting}
                inputProps={{ inputMode: 'numeric', maxLength: 6, pattern: '[0-9]*' }}
                label="Deletion OTP"
                onChange={(event) => setDeletionOtp(event.target.value.replace(/\D/g, ''))}
                value={deletionOtp}
              />
            </> : null}
            {deleteStep === 3 ? <Alert severity="error">
              <Typography sx={{ fontWeight: 700 }}>This is your final confirmation.</Typography>
              Deleting {organization?.name} will deactivate the organization and its team accounts. This deletion cannot be reversed.
            </Alert> : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button disabled={isDeleting} onClick={closeDeleteDialog}>Cancel</Button>
          {deleteStep === 1 ? <Button disabled={isDeleting} onClick={handleSendDeletionOtp} variant="contained">
            {isDeleting ? 'Sending OTP…' : 'Confirm and send OTP'}
          </Button> : null}
          {deleteStep === 2 ? <Button disabled={isDeleting || deletionOtp.length !== 6} onClick={() => setDeleteStep(3)} variant="contained">
            Continue
          </Button> : null}
          {deleteStep === 3 ? <Button
            color="error"
            disabled={isDeleting}
            onClick={handleDeleteOrganization}
            variant="contained"
          >
            {isDeleting ? 'Deleting…' : 'Permanently delete organization'}
          </Button> : null}
        </DialogActions>
      </Dialog>
    </Box>
  );
}
