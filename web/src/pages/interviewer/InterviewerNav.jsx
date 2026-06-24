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
    <Paper sx={{ p: 1.5, mb: 3 }}>
      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
        {links.map(([label, to]) => (
          <Button key={to} component={RouterLink} size="small" to={to} variant="text">
            {label}
          </Button>
        ))}
      </Stack>
    </Paper>
  );
}
