import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getApplications, rejectApplication } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { candidateFitFromScore } from './candidateFit.js';
import { applicationName, formatDateTime, getApiErrorMessage, scoreText, titleize } from './recruiterUtils.js';
import { renderApplicationTemplate } from './communicationTemplates.js';

function FitChip({ score }) {
  const fit = candidateFitFromScore(score);
  return (
    <Tooltip title={fit.description}>
      <Chip color={fit.color} label={fit.label} size="small" />
    </Tooltip>
  );
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    setIsLoading(true);
    try {
      setApplications(await getApplications());
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load applications.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    getApplications()
      .then((data) => {
        if (active) {
          setApplications(data);
        }
      })
      .catch((err) => {
        if (active) {
          setError(getApiErrorMessage(err, 'Unable to load applications.'));
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const reject = async (app) => {
    const defaultMessage = renderApplicationTemplate('rejection', app.status === 'evaluation_submitted' ? 'rejection_after_interview' : 'rejection_general', app);
    const reason = window.prompt('Candidate rejection message', defaultMessage);
    if (!reason) {
      return;
    }
    setBusyId(app.id);
    try {
      await rejectApplication(app.id, { reason, remark: reason });
      setSuccess('Candidate rejected.');
      load();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to reject candidate.'));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Applications</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Use AI fit labels as triage support only. Final shortlist and rejection decisions remain with the recruiter.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Candidate</TableCell>
              <TableCell>Job</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>AI fit</TableCell>
              <TableCell>Final score</TableCell>
              <TableCell>Applied</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {applications.map((app) => (
              <TableRow key={app.id}>
                <TableCell>{applicationName(app)}</TableCell>
                <TableCell>{app.job_title}</TableCell>
                <TableCell><Chip label={titleize(app.status)} size="small" /></TableCell>
                <TableCell><FitChip score={app.final_score} /></TableCell>
                <TableCell>{scoreText(app.final_score)}</TableCell>
                <TableCell>{formatDateTime(app.applied_at)}</TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button component={RouterLink} to={`/recruiter/applications/${app.id}`} size="small">Profile</Button>
                    {app.status !== 'rejected' ? (
                      <Button component={RouterLink} to={`/recruiter/applications/${app.id}/assign-interview`} size="small">
                        Assign
                      </Button>
                    ) : null}
                    {app.status !== 'rejected' ? (
                      <Button color="error" disabled={busyId === app.id} onClick={() => reject(app)} size="small">
                        Reject
                      </Button>
                    ) : null}
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && applications.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7}>No applications yet.</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
