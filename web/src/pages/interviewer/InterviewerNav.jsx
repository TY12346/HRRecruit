import { Button, Paper, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const links = [
  ['Dashboard', '/interviewer'],
  ['Candidates', '/interviewer/candidates'],
  ['Interviews', '/interviewer/interviews'],
  ['Availability', '/interviewer/availability'],
  ['Analytics', '/interviewer/analytics'],
  ['Notifications', '/interviewer/notifications'],
];

export default function InterviewerNav() {
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
        {links.map(([label, to]) => (
          <Button key={to} component={RouterLink} size="small" to={to} sx={{ justifyContent: { md: 'flex-start' } }} variant="text">
            {label}
          </Button>
        ))}
      </Stack>
    </Paper>
  );
}
