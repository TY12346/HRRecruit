import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getApplicantProfile, openApplicationResume, rejectApplication } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApplicationStatusInfo } from '../../utils/recruitmentFlow.js';
import { applicationName, getApiErrorMessage, titleize } from './recruiterUtils.js';
import { renderApplicationTemplate } from './communicationTemplates.js';

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

const formatEducationRows = (education) => {
  if (!education || typeof education !== 'object' || Array.isArray(education)) {
    return [formatExtractedValue(education)];
  }

  const rows = Object.entries(education)
    .map(([key, value]) => `${titleize(key)}: ${formatExtractedValue(value)}`)
    .filter((row) => !row.endsWith(`: ${EMPTY_EXTRACTION_VALUE}`));

  return rows.length ? rows : [EMPTY_EXTRACTION_VALUE];
};

export default function ApplicantProfilePage() {
  const { applicationId } = useParams();
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    setIsLoading(true);
    try {
      setProfile(await getApplicantProfile(applicationId));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load applicant profile.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    getApplicantProfile(applicationId)
      .then((applicant) => {
        if (active) setProfile(applicant);
      })
      .catch((err) => {
        if (active) setError(getApiErrorMessage(err, 'Unable to load applicant profile.'));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => { active = false; };
  }, [applicationId]);

  const reject = async () => {
    const defaultMessage = renderApplicationTemplate(
      'rejection',
      profile?.status === 'evaluation_submitted' ? 'rejection_after_interview' : 'rejection_general',
      profile ?? {},
    );
    const reason = window.prompt('Applicant rejection message', defaultMessage);
    if (!reason) return;

    try {
      await rejectApplication(applicationId, { reason, remark: reason });
      setSuccess('Applicant rejected.');
      load();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to reject applicant.'));
    }
  };

  const viewResume = async () => {
    try {
      await openApplicationResume(applicationId);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to open resume.'));
    }
  };

  const applicant = profile?.applicant_profile;

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
                <Chip label={`Current stage: ${getApplicationStatusInfo(profile.status, 'recruiter').label}`} sx={{ mt: 1 }} />
              </Box>
              {profile.status !== 'rejected' ? (
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  <Button component={RouterLink} to={`/recruiter/applications/${applicationId}/assign-interview`} variant="outlined">
                    Assign interviewer
                  </Button>
                  <Button color="error" onClick={reject} variant="outlined">Reject</Button>
                </Stack>
              ) : null}
            </Stack>

            <Card>
              <CardContent>
                <Typography variant="h6">Resume extraction</Typography>
                <Stack spacing={1.5} sx={{ mt: 1 }}>
                  <Typography><strong>Skills:</strong> {(profile.extracted_skills ?? []).join(', ') || EMPTY_EXTRACTION_VALUE}</Typography>
                  <Typography><strong>Experience:</strong> {formatExtractedValue(profile.resume_info?.extracted_experience)}</Typography>
                  <Box>
                    <Typography component="div"><strong>Education:</strong></Typography>
                    {formatEducationRows(profile.resume_info?.extracted_education).map((row, index) => (
                      <Typography key={`${row}-${index}`} sx={{ ml: 2 }}>{row}</Typography>
                    ))}
                  </Box>
                  {profile.resume_info?.resume_file ? <Button onClick={viewResume} sx={{ alignSelf: 'flex-start' }}>View resume</Button> : null}
                </Stack>
              </CardContent>
            </Card>
          </Stack>
        ) : null}
      </Paper>
    </Box>
  );
}
