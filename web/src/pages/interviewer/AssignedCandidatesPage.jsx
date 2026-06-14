import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getAssignedInterviews } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { candidateName, formatDateTime, getApiErrorMessage, jobTitle, latestInviteStatus, titleize } from './interviewerUtils.js';

export default function AssignedCandidatesPage() {
  const [interviews, setInterviews] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => { getAssignedInterviews().then(setInterviews).catch((err) => setError(getApiErrorMessage(err, 'Unable to load assigned candidates.'))).finally(() => setIsLoading(false)); }, []);

  return (
    <Box><InterviewerNav /><Paper sx={{ p: 3 }}><Typography variant="h5" sx={{ fontWeight: 700 }}>Assigned Candidates</Typography>{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{isLoading ? <CircularProgress /> : null}<Stack spacing={2}>{interviews.map((interview) => <Card key={interview.id} variant="outlined"><CardContent><Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}><Box><Typography variant="h6">{candidateName(interview)}</Typography><Typography>{jobTitle(interview)} • {titleize(interview.application?.status)}</Typography><Typography color="text.secondary">Recruiter remark: {interview.application?.recruiter_remark || '—'}</Typography><Typography color="text.secondary">Invitation: {latestInviteStatus(interview)} • {formatDateTime(interview.latest_invitation?.proposed_datetime)}</Typography></Box><Stack direction="row" spacing={1}><Button component={RouterLink} to={`/interviewer/candidates/${interview.application?.id}`} variant="outlined">Candidate detail</Button><Button component={RouterLink} to={`/interviewer/interviews/${interview.id}/invitation`} variant="contained">Send invitation</Button></Stack></Stack></CardContent></Card>)}{!isLoading && interviews.length === 0 ? <Typography color="text.secondary">No assigned candidates yet.</Typography> : null}</Stack></Paper></Box>
  );
}
