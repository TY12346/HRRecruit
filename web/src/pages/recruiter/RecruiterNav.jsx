import { Button, Paper, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const recruiterLinks = [
  ['Dashboard', '/recruiter'],
  ['Jobs', '/recruiter/jobs'],
  ['Applications', '/recruiter/applications'],
  ['Interviews', '/recruiter/interviews'],
  ['Decisions', '/recruiter/hiring-decisions'],
  ['Offers', '/recruiter/job-offers'],
  ['Analytics', '/recruiter/analytics'],
  ['Notifications', '/recruiter/notifications'],
];

export default function RecruiterNav() {
  return (
    <Paper sx={{ p: 1.5, mb: 3 }}>
      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
        {recruiterLinks.map(([label, to]) => (
          <Button key={to} component={RouterLink} size="small" to={to} variant="text">
            {label}
          </Button>
        ))}
      </Stack>
    </Paper>
  );
}
