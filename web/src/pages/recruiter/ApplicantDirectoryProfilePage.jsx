import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Link,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getApplicantDirectoryProfile } from '../../api/client.js';
import Alert from '../../components/TimedAlert.jsx';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';

const displayDate = (value) => value || 'Not specified';

export default function ApplicantDirectoryProfilePage() {
  const { applicantId } = useParams();
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError('');
    getApplicantDirectoryProfile(applicantId)
      .then((data) => { if (active) setProfile(data); })
      .catch((requestError) => { if (active) setError(getApiErrorMessage(requestError, 'Unable to load applicant profile.')); })
      .finally(() => { if (active) setIsLoading(false); });
    return () => { active = false; };
  }, [applicantId]);

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Button component={RouterLink} to="/recruiter/applicant-search" sx={{ mb: 2 }}>Back to applicant search</Button>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        {profile ? (
          <Stack spacing={3}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{profile.full_name}</Typography>
              <Typography color="text.secondary">{profile.email}</Typography>
              <Typography color="text.secondary">{profile.phone_number || 'No phone number provided'}</Typography>
              {profile.linkedin_url ? <Link href={profile.linkedin_url} target="_blank" rel="noreferrer">LinkedIn profile</Link> : null}
            </Box>

            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Profile Summary</Typography>
                <Typography sx={{ whiteSpace: 'pre-wrap' }}>{profile.personal_summary || 'No profile summary provided.'}</Typography>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Skills</Typography>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  {profile.skills.length ? profile.skills.map((skill) => <Chip key={skill} label={skill} />) : <Typography>No skills provided.</Typography>}
                </Stack>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Experience</Typography>
                {profile.experiences.length ? profile.experiences.map((experience, index) => (
                  <Box key={`${experience.job_title}-${experience.company_name}-${index}`} sx={{ py: 1.5 }}>
                    {index ? <Divider sx={{ mb: 2 }} /> : null}
                    <Typography sx={{ fontWeight: 700 }}>{experience.job_title}</Typography>
                    <Typography>{experience.company_name || 'Company not specified'}</Typography>
                    <Typography color="text.secondary">{experience.employment_type || 'Employment type not specified'}</Typography>
                    <Typography color="text.secondary">Started: {displayDate(experience.start_date)}</Typography>
                    <Typography color="text.secondary">Location: {experience.location || 'Not specified'}</Typography>
                  </Box>
                )) : <Typography>No experience provided.</Typography>}
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Education</Typography>
                {profile.educations.length ? profile.educations.map((education, index) => (
                  <Box key={`${education.school_name}-${education.degree_name}-${index}`} sx={{ py: 1.5 }}>
                    {index ? <Divider sx={{ mb: 2 }} /> : null}
                    <Typography sx={{ fontWeight: 700 }}>{education.degree_name || 'Degree not specified'}</Typography>
                    <Typography>{education.field_of_study || 'Field of study not specified'}</Typography>
                    <Typography>{education.school_name}</Typography>
                    <Typography color="text.secondary">{displayDate(education.start_date)} – {displayDate(education.end_date)}</Typography>
                    <Typography color="text.secondary">Grade: {education.grade || 'Not specified'}</Typography>
                  </Box>
                )) : <Typography>No education provided.</Typography>}
              </CardContent>
            </Card>
          </Stack>
        ) : null}
      </Paper>
    </Box>
  );
}
