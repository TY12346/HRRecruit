import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, CircularProgress, Grid, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getAssignedInterviews, getCandidateProfile, openApplicationResume } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './interviewerUtils.js';

export default function CandidateDetailPage() {
  const { applicationId } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [interview, setInterview] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    Promise.all([getCandidateProfile(applicationId), getAssignedInterviews()])
      .then(([profile, interviews]) => { setCandidate(profile); setInterview(interviews.find((item) => String(item.application?.id) === String(applicationId)) ?? null); })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load candidate detail.')))
      .finally(() => setIsLoading(false));
  }, [applicationId]);
  const applicant = candidate?.applicant_profile ?? {};
  const resume = candidate?.resume_info ?? {};
  const openResume = async () => { try { await openApplicationResume(applicationId); } catch (err) { setError(getApiErrorMessage(err, 'Unable to open resume.')); } };
  return <Box><InterviewerNav /><Paper sx={{ p: 3 }}><Typography variant="h5" sx={{ fontWeight: 700 }}>Candidate Detail</Typography>{error ? <Alert severity="error" sx={{ my: 2 }}>{error}</Alert> : null}{isLoading ? <CircularProgress /> : null}{candidate ? <Stack spacing={2} sx={{ mt: 2 }}><Card variant="outlined"><CardContent><Typography variant="h6">{applicant.full_name}</Typography><Typography color="text.secondary">{applicant.email} • {applicant.phone_number || 'No phone'}</Typography><Typography>Application status: {titleize(candidate.status)}</Typography><Typography>Applied: {formatDateTime(candidate.applied_at)}</Typography><Typography>Recruiter remark: {candidate.recruiter_remark || '—'}</Typography>{applicant.linkedin_url ? <Button href={applicant.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</Button> : null}{resume.resume_file ? <Button onClick={openResume}>Open resume</Button> : null}</CardContent></Card><Grid container spacing={2}><Grid item xs={12} md={6}><Card variant="outlined"><CardContent><Typography variant="h6">Resume extraction</Typography><Typography><strong>Skills:</strong> {(candidate.extracted_skills ?? []).join(', ') || '—'}</Typography><Typography><strong>Experience:</strong> {resume.extracted_experience || '—'}</Typography><Typography><strong>Education:</strong> {resume.extracted_education || '—'}</Typography></CardContent></Card></Grid><Grid item xs={12} md={6}><Card variant="outlined"><CardContent><Typography variant="h6">AI scores</Typography>{Object.entries(candidate.scores ?? {}).map(([key, value]) => <Typography key={key}>{titleize(key)}: {value ?? '—'}</Typography>)}</CardContent></Card></Grid></Grid><Card variant="outlined"><CardContent><Typography variant="h6">Personal summary</Typography><Typography whiteSpace="pre-line">{applicant.personal_summary || '—'}</Typography></CardContent></Card>{interview ? <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap"><Button component={RouterLink} to={`/interviewer/interviews/${interview.id}/invitation`} variant="contained">Send invitation</Button><Button component={RouterLink} to={`/interviewer/interviews/${interview.id}`} variant="outlined">Open interview</Button></Stack> : null}</Stack> : null}</Paper></Box>;
}
