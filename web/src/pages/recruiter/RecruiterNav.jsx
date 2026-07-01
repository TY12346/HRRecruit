import { Button, Paper, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const recruiterLinks = [
  ['Dashboard', '/recruiter'],
  ['Jobs', '/recruiter/jobs'],
  ['Interviews', '/recruiter/interviews'],
  ['Decisions', '/recruiter/hiring-decisions'],
  ['Offers', '/recruiter/job-offers'],
  ['Analytics', '/recruiter/analytics'],
  ['Notifications', '/recruiter/notifications'],
];

export default function RecruiterNav() {
  return (
    <Paper
      component="nav"
      sx={{
        bottom: { md: 0 },
        left: { md: 0 },
        mb: { xs: 3, md: 0 },
        overflowY: { md: 'auto' },
        p: 1.5,
        position: { xs: 'static', md: 'fixed' },
        top: { md: 0 },
        width: { md: 220 },
        zIndex: (theme) => theme.zIndex.drawer,
      }}
    >
      <Stack direction={{ xs: 'row', md: 'column' }} spacing={1} useFlexGap flexWrap={{ xs: 'wrap', md: 'nowrap' }}>
        {recruiterLinks.map(([label, to]) => (
          <Button key={to} component={RouterLink} size="small" to={to} sx={{ justifyContent: { md: 'flex-start' } }} variant="text">
            {label}
          </Button>
        ))}
      </Stack>
    </Paper>
  );
}
