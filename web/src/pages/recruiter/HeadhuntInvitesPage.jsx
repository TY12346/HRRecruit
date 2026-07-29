import { useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import RecruiterNav from './RecruiterNav.jsx';
import Alert from '../../components/TimedAlert.jsx';
import { getEmployerInvites } from '../../api/client.js';

const responseLabel = (value) => (
  value === 'applied' ? 'Applied for job' : value === 'declined' ? 'Declined' : 'No response'
);

export default function HeadhuntInvitesPage() {
  const [invites, setInvites] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [applicantFilter, setApplicantFilter] = useState('');
  const [jobFilter, setJobFilter] = useState('');
  const [responseFilter, setResponseFilter] = useState('');

  useEffect(() => {
    getEmployerInvites()
      .then(setInvites)
      .catch(() => setError('Unable to load headhunt invites.'))
      .finally(() => setLoading(false));
  }, []);

  const applicants = useMemo(() => (
    [...new Map(invites.map((invite) => [invite.applicant, invite])).values()]
  ), [invites]);
  const jobs = useMemo(() => (
    [...new Map(invites.map((invite) => [invite.job, invite])).values()]
  ), [invites]);
  const filteredInvites = useMemo(() => invites.filter((invite) => (
    (!applicantFilter || String(invite.applicant) === applicantFilter)
    && (!jobFilter || String(invite.job) === jobFilter)
    && (!responseFilter || invite.response === responseFilter)
  )), [applicantFilter, invites, jobFilter, responseFilter]);

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" fontWeight={700}>Headhunt Invites</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Track employer invitations you have sent to applicants.
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        {loading ? <CircularProgress /> : (
          <>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
              <TextField
                select
                label="Applicant"
                value={applicantFilter}
                onChange={(event) => setApplicantFilter(event.target.value)}
                sx={{ minWidth: 220 }}
              >
                <MenuItem value="">All applicants</MenuItem>
                {applicants.map((invite) => (
                  <MenuItem key={invite.applicant} value={String(invite.applicant)}>
                    {invite.applicant_name}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Job"
                value={jobFilter}
                onChange={(event) => setJobFilter(event.target.value)}
                sx={{ minWidth: 220 }}
              >
                <MenuItem value="">All jobs</MenuItem>
                {jobs.map((invite) => (
                  <MenuItem key={invite.job} value={String(invite.job)}>{invite.job_title}</MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Response type"
                value={responseFilter}
                onChange={(event) => setResponseFilter(event.target.value)}
                sx={{ minWidth: 180 }}
              >
                <MenuItem value="">All responses</MenuItem>
                {['no_response', 'applied', 'declined'].map((response) => (
                  <MenuItem key={response} value={response}>{responseLabel(response)}</MenuItem>
                ))}
              </TextField>
            </Stack>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Applicant</TableCell>
                    <TableCell>Job</TableCell>
                    <TableCell>Response</TableCell>
                    <TableCell>Sent at</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredInvites.map((invite) => (
                    <TableRow key={invite.id}>
                      <TableCell>
                        <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
                          <Box>
                            {invite.applicant_name}<br />
                            <Typography variant="caption">{invite.applicant_email}</Typography>
                          </Box>
                          <Button
                            component={RouterLink}
                            to={`/recruiter/applicant-search/${invite.applicant}`}
                            variant="outlined"
                            size="small"
                          >
                            View profile
                          </Button>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
                          <Typography>{invite.job_title}</Typography>
                          <Button
                            component={RouterLink}
                            to={`/recruiter/jobs/${invite.job}`}
                            variant="outlined"
                            size="small"
                          >
                            View job
                          </Button>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={responseLabel(invite.response)}
                          color={invite.response === 'applied' ? 'success' : invite.response === 'declined' ? 'default' : 'warning'}
                        />
                      </TableCell>
                      <TableCell>{new Date(invite.created_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                  {!filteredInvites.length && (
                    <TableRow>
                      <TableCell colSpan={4}>
                        {invites.length ? 'No invites match the selected filters.' : 'No headhunt invites sent yet.'}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </Paper>
    </Box>
  );
}
