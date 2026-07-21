import { useEffect, useState } from 'react';
import { Box, Chip, CircularProgress, Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { getJobHiringRecommendations } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

export default function HiringRecommendationsPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getJobHiringRecommendations()
      .then(setRecommendations)
      .catch((loadError) => setError(getApiErrorMessage(loadError, 'Unable to load hiring recommendations.')))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
          Hiring Recommendations
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Track the job-level hiring recommendations you submitted for hiring manager review.
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress aria-label="Loading hiring recommendations" /> : null}

        <Table sx={{ mt: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>Job</TableCell>
              <TableCell>Recommendation</TableCell>
              <TableCell>Selected applicants</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Submitted</TableCell>
              <TableCell>Hiring manager remarks</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {recommendations.map((recommendation) => (
              <TableRow key={recommendation.id}>
                <TableCell>{recommendation.job_title}</TableCell>
                <TableCell>{titleize(recommendation.recommendation_type)}</TableCell>
                <TableCell>{recommendation.items.length}</TableCell>
                <TableCell>
                  <Chip
                    color={recommendation.status === 'approved' ? 'success' : recommendation.status === 'rejected' ? 'error' : 'warning'}
                    label={titleize(recommendation.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{formatDateTime(recommendation.submitted_at)}</TableCell>
                <TableCell>{recommendation.hr_remarks || '—'}</TableCell>
              </TableRow>
            ))}
            {!isLoading && recommendations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6}>No hiring recommendations yet.</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
