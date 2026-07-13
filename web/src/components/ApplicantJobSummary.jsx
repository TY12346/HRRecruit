import { Stack, Typography } from '@mui/material';

export default function ApplicantJobSummary({ applicantName = '—', jobTitle = '—', variant = 'body1', labelWidth = 'auto' }) {
  return (
    <Stack spacing={0.25}>
      <Typography variant={variant}>
        <Typography component="span" variant={variant} sx={{ fontWeight: 700, minWidth: labelWidth, display: labelWidth === 'auto' ? 'inline' : 'inline-block' }}>
          Applicant name:
        </Typography>{' '}
        {applicantName || '—'}
      </Typography>
      <Typography variant={variant}>
        <Typography component="span" variant={variant} sx={{ fontWeight: 700, minWidth: labelWidth, display: labelWidth === 'auto' ? 'inline' : 'inline-block' }}>
          Job applied:
        </Typography>{' '}
        {jobTitle || '—'}
      </Typography>
    </Stack>
  );
}
