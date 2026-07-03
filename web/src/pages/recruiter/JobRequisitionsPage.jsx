import { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getJobRequisitions } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

const departmentName = (item) => (item.department === 'Other' ? item.custom_department : item.department) || '—';

export default function JobRequisitionsPage() {
  const [requisitions, setRequisitions] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getJobRequisitions()
      .then(setRequisitions)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load job requisitions.')))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <Box>
      <RecruiterNav />
      <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 2 }}>Job Requisitions</Typography>
      <Button component={RouterLink} to="/recruiter/jobs/create" variant="contained" sx={{ mb: 2 }}>Create requisition</Button>
      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
      {isLoading ? <CircularProgress /> : null}
      <Stack spacing={0} sx={{ mt: 2 }}>
        {requisitions.map((item) => (
          <Stack key={item.id} direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1} sx={{ py: 1, borderTop: '1px solid', borderColor: 'divider', '&:first-of-type': { borderTop: 0 } }}>
            <Box>
              <Typography sx={{ fontWeight: 700 }}>{item.title}</Typography>
              <Typography color="text.secondary" variant="body2">
                {departmentName(item)} • {item.location} • {titleize(item.employment_type)} • {item.salary_range || 'Salary range not specified'}
              </Typography>
              <Typography color="text.secondary" variant="body2">
                {titleize(item.position_status)} • Target start {item.target_start_date || 'not specified'} • Submitted {formatDateTime(item.created_at)}
              </Typography>
              {item.status === 'rejected' ? <Typography color="error" variant="body2">Reason: {item.rejection_reason}</Typography> : null}
              {item.status === 'approved' && item.job_posting_id ? <Typography color="text.secondary" variant="body2">Draft job #{item.job_posting_id}</Typography> : null}
            </Box>
            <Chip label={titleize(item.status)} size="small" color={item.status === 'approved' ? 'success' : item.status === 'rejected' ? 'error' : 'warning'} sx={{ alignSelf: { xs: 'flex-start', md: 'center' } }} />
          </Stack>
        ))}
        {!isLoading && requisitions.length === 0 ? <Typography color="text.secondary">No job requisitions yet.</Typography> : null}
      </Stack>
    </Box>
  );
}
