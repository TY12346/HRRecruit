import { Box, Button, Paper, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const links = [
  ['⌂', 'Dashboard', '/interviewer'],
  ['☷', 'Candidates', '/interviewer/candidates'],
  ['◷', 'Interviews', '/interviewer/interviews'],
  ['▣', 'Availability', '/interviewer/availability'],
  ['◔', 'Analytics', '/interviewer/analytics'],
  ['♧', 'Notifications', '/interviewer/notifications'],
];

export default function InterviewerNav() {
  return (
    <Paper
      component="nav"
      elevation={0}
      square
      sx={{
        bgcolor: '#ffffff',
        borderRight: { md: '1px solid #e5e7eb' },
        bottom: { md: 0 },
        left: { md: 0 },
        mb: { xs: 4, md: 0 },
        overflowY: { md: 'auto' },
        position: { xs: 'static', md: 'fixed' },
        pt: { xs: 0, md: 3 },
        top: { md: 64 },
        width: { md: 230 },
        zIndex: (theme) => theme.zIndex.drawer,
      }}
    >
      <Stack direction={{ xs: 'row', md: 'column' }} spacing={1.5} useFlexGap flexWrap={{ xs: 'wrap', md: 'nowrap' }}>
        {links.map(([icon, label, to]) => (
          <Button
            key={to}
            component={RouterLink}
            size="small"
            to={to}
            variant="text"
            sx={{
              color: '#111111',
              fontSize: 12,
              fontWeight: 800,
              gap: 1,
              justifyContent: { xs: 'center', md: 'flex-start' },
              minHeight: 46,
              px: { xs: 1.75, md: 2.5 },
              textTransform: 'none',
            }}
          >
            <Box component="span" sx={{ fontSize: 17, fontWeight: 400, lineHeight: 1, width: 18 }}>
              {icon}
            </Box>
            {label}
          </Button>
        ))}
      </Stack>
    </Paper>
  );
}
