import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useParams } from 'react-router-dom';
import { getApplications, submitHiringDecision } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { applicationName, getApiErrorMessage, scoreText } from './recruiterUtils.js';
import ApplicationFlowSummary from '../../components/ApplicationFlowSummary.jsx';
import { getApplicationStatusInfo } from '../../utils/recruitmentFlow.js';

const EVALUATED_STATUS = 'evaluation_submitted';

export default function HiringDecisionPage() {
  const { applicationId } = useParams();
  const [applications, setApplications] = useState([]);
  const [selectedId, setSelectedId] = useState(applicationId ?? '');
  const [decision, setDecision] = useState('hire');
  const [justification, setJustification] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const evaluatedApplications = useMemo(
    () => applications.filter((app) => app.status === EVALUATED_STATUS),
    [applications],
  );
  const selected = applications.find((item) => String(item.id) === String(selectedId));
  const selectedIsEligible = selected?.status === EVALUATED_STATUS;

  useEffect(() => {
    getApplications()
      .then((items) => {
        setApplications(items);
        const routeSelected = items.find((item) => String(item.id) === String(applicationId));
        if (routeSelected) {
          setSelectedId(String(routeSelected.id));
          return;
        }
        const firstEvaluated = items.find((item) => item.status === EVALUATED_STATUS);
        if (firstEvaluated) setSelectedId(String(firstEvaluated.id));
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load applications.')))
      .finally(() => setIsLoading(false));
  }, [applicationId]);

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    if (!selectedIsEligible) {
      setError('Select a candidate with a completed interview evaluation before submitting a hiring decision.');
      return;
    }
    try {
      const result = await submitHiringDecision(selectedId, { decision, justification });
      setSuccess(`Hiring decision #${result.id} submitted for HR approval.`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to submit hiring decision.'));
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Hiring decision</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Submit hire or reject recommendations only after interview evaluation is complete. AI supports the decision but does not finalize it.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        {isLoading ? <CircularProgress /> : (
          <Stack spacing={3}>
            {evaluatedApplications.length === 0 ? (
              <Alert severity="info">
                No evaluated candidates are available yet. Ask the interviewer to submit the interview evaluation before creating a hiring decision.
              </Alert>
            ) : null}
            {selected && !selectedIsEligible ? (
              <Alert severity="warning">
                {applicationName(selected)} is currently {getApplicationStatusInfo(selected.status, 'recruiter').label}. Hiring decisions are enabled only after the interviewer submits the evaluation.
              </Alert>
            ) : null}
            <Box component="form" onSubmit={submit}>
              <Stack spacing={2}>
                <TextField
                  label="Evaluated candidate"
                  select
                  required
                  value={selectedId}
                  onChange={(e) => setSelectedId(e.target.value)}
                  disabled={evaluatedApplications.length === 0 && !selected}
                >
                  {selected && !selectedIsEligible ? (
                    <MenuItem value={selectedId} disabled>
                      {applicationName(selected)} — {selected.job_title} (evaluation not complete)
                    </MenuItem>
                  ) : null}
                  {evaluatedApplications.map((app) => (
                    <MenuItem key={app.id} value={app.id}>{applicationName(app)} — {app.job_title}</MenuItem>
                  ))}
                </TextField>
                {selectedIsEligible ? (
                  <ApplicationFlowSummary status={selected.status} role="recruiter" compact />
                ) : null}
                <TextField label="Decision" select value={decision} onChange={(e) => setDecision(e.target.value)} disabled={!selectedIsEligible}>
                  <MenuItem value="hire">Recommend hire</MenuItem>
                  <MenuItem value="reject">Recommend reject</MenuItem>
                </TextField>
                <TextField
                  label="Justification for HR"
                  required
                  multiline
                  minRows={4}
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  disabled={!selectedIsEligible}
                />
                <Button type="submit" variant="contained" disabled={!selectedIsEligible}>Submit for HR approval</Button>
              </Stack>
            </Box>
            <Typography variant="h6">Evaluated candidates</Typography>
            <Table>
              <TableHead>
                <TableRow><TableCell>Candidate</TableCell><TableCell>Job</TableCell><TableCell>Status</TableCell><TableCell>Score</TableCell></TableRow>
              </TableHead>
              <TableBody>
                {evaluatedApplications.slice(0, 8).map((app) => (
                  <TableRow key={app.id}>
                    <TableCell>{applicationName(app)}</TableCell>
                    <TableCell>{app.job_title}</TableCell>
                    <TableCell><Chip label={getApplicationStatusInfo(app.status, 'recruiter').label} size="small" color="success" /></TableCell>
                    <TableCell>{scoreText(app.final_score)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Stack>
        )}
      </Paper>
    </Box>
  );
}
