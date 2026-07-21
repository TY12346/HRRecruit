import { useEffect, useState } from 'react';
import { Box, Chip, CircularProgress, Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { getJobHiringDecisions } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

export default function HiringDecisionsPage() {
  const [decisions, setDecisions] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getJobHiringDecisions()
      .then(setDecisions)
      .catch((loadError) => setError(getApiErrorMessage(loadError, 'Unable to load hiring decisions.')))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
          Hiring Decisions
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Track the job-level hiring decisions you submitted for hiring manager review.
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading hiring decisions" /> : null}

        <Table sx={{ mt: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>Job</TableCell>
              <TableCell>Decision</TableCell>
              <TableCell>Selected applicants</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Submitted</TableCell>
              <TableCell>Hiring manager remarks</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {decisions.map((decision) => (
              <TableRow key={decision.id}>
                <TableCell>{decision.job_title}</TableCell>
                <TableCell>{titleize(decision.decision_type)}</TableCell>
                <TableCell>{decision.items.length}</TableCell>
                <TableCell>
                  <Chip
                    color={decision.status === 'approved' ? 'success' : decision.status === 'rejected' ? 'error' : 'warning'}
                    label={titleize(decision.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{formatDateTime(decision.submitted_at)}</TableCell>
                <TableCell>{decision.hr_remarks || '—'}</TableCell>
              </TableRow>
            ))}
            {!isLoading && decisions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6}>No hiring decisions yet.</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
