import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getApplicationStatusHistory, getCandidateProfile, openApplicationResume, rejectApplication } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { applicationName, formatDateTime, getApiErrorMessage, scoreText, titleize } from './recruiterUtils.js';
import { renderApplicationTemplate } from './communicationTemplates.js';
import { buildScreeningExplainability } from './screeningExplainability.js';

const EMPTY_EXTRACTION_VALUE = '—';

const formatExtractedValue = (value) => {
  if (value === null || value === undefined || value === '') return EMPTY_EXTRACTION_VALUE;
  if (Array.isArray(value)) {
    const items = value.map(formatExtractedValue).filter((item) => item !== EMPTY_EXTRACTION_VALUE);
    return items.length ? items.join(', ') : EMPTY_EXTRACTION_VALUE;
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value)
      .map(([key, nestedValue]) => [key, formatExtractedValue(nestedValue)])
      .filter(([, formattedValue]) => formattedValue !== EMPTY_EXTRACTION_VALUE);
    return entries.length
      ? entries.map(([key, formattedValue]) => `${titleize(key)}: ${formattedValue}`).join('; ')
      : EMPTY_EXTRACTION_VALUE;
  }
  return String(value);
};

function ScreeningExplanationCard({ explainability }) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1.5}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
            <Typography variant="h6">AI screening explanation</Typography>
            <Chip color={explainability.fit.color} label={explainability.fit.label} size="small" />
          </Stack>

          <Alert severity="info">
            AI screening is decision support only. Review the evidence below before shortlisting or rejecting this candidate.
          </Alert>

          <Box>
            <Typography variant="body2" color="text.secondary">Overall resume fit</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{scoreText(explainability.finalScore)}</Typography>
            <Typography variant="body2" color="text.secondary">{explainability.fit.description}</Typography>
          </Box>

          <Divider />

          {explainability.scoreComponents.map((component) => (
            <Box key={component.key}>
              <Stack direction="row" justifyContent="space-between" spacing={1}>
                <Typography variant="subtitle2">{component.label}</Typography>
                <Typography variant="subtitle2">{scoreText(component.value)}</Typography>
              </Stack>
              <LinearProgress variant="determinate" value={component.percent} sx={{ my: 0.75, height: 8, borderRadius: 1 }} />
              <Typography variant="caption" color="text.secondary">{component.description}</Typography>
            </Box>
          ))}

          <Divider />

          <Grid container spacing={1.5}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2">Matched evidence</Typography>
              <Stack direction="row" spacing={0.5} useFlexGap flexWrap="wrap" sx={{ mt: 0.75 }}>
                {explainability.matchedSkills.length ? (
                  explainability.matchedSkills.map((skill) => <Chip key={skill} label={skill} size="small" color="success" variant="outlined" />)
                ) : (
                  <Typography variant="body2" color="text.secondary">No matched skills recorded.</Typography>
                )}
              </Stack>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2">Missing / review items</Typography>
              <Stack direction="row" spacing={0.5} useFlexGap flexWrap="wrap" sx={{ mt: 0.75 }}>
                {explainability.missingSkills.length ? (
                  explainability.missingSkills.map((skill) => <Chip key={skill} label={skill} size="small" color="warning" variant="outlined" />)
                ) : (
                  <Typography variant="body2" color="text.secondary">No missing skills recorded.</Typography>
                )}
              </Stack>
            </Grid>
          </Grid>

          {explainability.positiveFactors.length || explainability.negativeFactors.length ? (
            <>
              <Divider />
              <Grid container spacing={1.5}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Positive factors</Typography>
                  <List dense>
                    {explainability.positiveFactors.map((factor) => (
                      <ListItem key={factor} disableGutters><ListItemText primary={factor} /></ListItem>
                    ))}
                  </List>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Risk factors</Typography>
                  <List dense>
                    {explainability.negativeFactors.map((factor) => (
                      <ListItem key={factor} disableGutters><ListItemText primary={factor} /></ListItem>
                    ))}
                  </List>
                </Grid>
              </Grid>
            </>
          ) : null}

          <Divider />

          <Stack spacing={0.5}>
            <Typography variant="caption" color="text.secondary">
              Model: {explainability.modelVersion}{explainability.fallbackUsed ? ' · deterministic fallback used' : ''}
            </Typography>
            {explainability.mlMatchLabel ? (
              <Typography variant="caption" color="text.secondary">
                ML label: {explainability.mlMatchLabel}
                {explainability.mlSuitabilityScore !== null ? ` · ML score ${scoreText(explainability.mlSuitabilityScore)}` : ''}
                {explainability.confidence !== null ? ` · confidence ${scoreText(explainability.confidence)}` : ''}
              </Typography>
            ) : null}
            {explainability.hybridFormula ? (
              <Typography variant="caption" color="text.secondary">Hybrid formula: {explainability.hybridFormula}</Typography>
            ) : null}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function CandidateProfilePage() {
  const { applicationId } = useParams();
  const [profile, setProfile] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    setIsLoading(true);
    try {
      const [candidate, timeline] = await Promise.all([
        getCandidateProfile(applicationId),
        getApplicationStatusHistory(applicationId),
      ]);
      setProfile(candidate);
      setHistory(timeline);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load candidate profile.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    Promise.all([getCandidateProfile(applicationId), getApplicationStatusHistory(applicationId)])
      .then(([candidate, timeline]) => {
        if (!active) return;
        setProfile(candidate);
        setHistory(timeline);
      })
      .catch((err) => {
        if (active) setError(getApiErrorMessage(err, 'Unable to load candidate profile.'));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => { active = false; };
  }, [applicationId]);

  const reject = async () => {
    const defaultMessage = renderApplicationTemplate('rejection', profile?.status === 'evaluation_submitted' ? 'rejection_after_interview' : 'rejection_general', profile ?? {});
    const reason = window.prompt('Candidate rejection message', defaultMessage);
    if (!reason) return;
    try {
      await rejectApplication(applicationId, { reason, remark: reason });
      setSuccess('Candidate rejected.');
      load();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to reject candidate.'));
    }
  };

  const openResume = async () => {
    try {
      await openApplicationResume(applicationId);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to open resume.'));
    }
  };

  const applicant = profile?.applicant_profile;
  const explainability = buildScreeningExplainability(profile ?? {});

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        {profile ? (
          <Stack spacing={3}>
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>{applicationName(profile)}</Typography>
                <Typography color="text.secondary">{applicant?.email} • {applicant?.phone_number || 'No phone'}</Typography>
                <Chip label={titleize(profile.status)} sx={{ mt: 1 }} />
              </Box>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                {profile.status !== 'rejected' ? <Button component={RouterLink} to={`/recruiter/applications/${applicationId}/assign-interview`} variant="outlined">Assign interviewer</Button> : null}
                {profile.status !== 'rejected' ? <Button component={RouterLink} to={`/recruiter/applications/${applicationId}/hiring-decision`} variant="outlined">Hiring decision</Button> : null}
                {profile.status !== 'rejected' ? <Button color="error" onClick={reject} variant="outlined">Reject</Button> : null}
              </Stack>
            </Stack>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">Resume and AI extraction</Typography>
                    <Typography><strong>Skills:</strong> {(profile.extracted_skills ?? []).join(', ') || '—'}</Typography>
                    <Typography><strong>Experience:</strong> {formatExtractedValue(profile.resume_info?.extracted_experience)}</Typography>
                    <Typography><strong>Education:</strong> {formatExtractedValue(profile.resume_info?.extracted_education)}</Typography>
                    {profile.resume_info?.resume_file ? <Button onClick={openResume}>Open resume</Button> : null}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <ScreeningExplanationCard explainability={explainability} />
              </Grid>
            </Grid>

            <Box>
              <Typography variant="h6">Stage history</Typography>
              <List>
                {history.map((item) => (
                  <ListItem key={item.id}>
                    <ListItemText
                      primary={`${titleize(item.from_stage)} → ${titleize(item.to_stage)}`}
                      secondary={`${item.note || 'No note'} • ${item.changed_by_name || 'System'} • ${formatDateTime(item.changed_at)}`}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          </Stack>
        ) : null}
      </Paper>
    </Box>
  );
}
