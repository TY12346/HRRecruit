import { Box, Button, Paper, Stack } from '@mui/material';
import { NavLink } from 'react-router-dom';

const navItems = [
  { icon: '⌂', label: 'Dashboard', to: '/hr-head' },
  { icon: '☷', label: 'Submitted Hiring Decisions', to: '/hr-head/hiring-decisions' },
  { icon: '◔', label: 'Analytics', to: '/hr-head/analytics' },
  { icon: '▱', label: 'Recruiter & Interviewer', to: '/hr-head/team' },
  { icon: '▣', label: 'Organization Account', to: '/hr-head/organization' },
  { icon: '□', label: 'Billing', to: '/hr-head/billing' },
  { icon: '♧', label: 'Notifications', to: '/hr-head/notifications' },
];

export default function HRHeadNav() {
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
        mb: { xs: 3, md: 0 },
        overflowY: { md: 'auto' },
        position: { xs: 'static', md: 'fixed' },
        pt: { xs: 0, md: 2 },
        top: { md: 64 },
        width: { md: 230 },
        zIndex: (theme) => theme.zIndex.drawer,
      }}
    >
      <Stack direction={{ xs: 'row', md: 'column' }} spacing={0.75} useFlexGap flexWrap={{ xs: 'wrap', md: 'nowrap' }}>
        {navItems.map((item) => (
          <Button
            component={NavLink}
            end={item.to === '/hr-head'}
            key={item.to}
            to={item.to}
            sx={{
              color: '#111111',
              fontSize: 12,
              fontWeight: 800,
              gap: 1,
              justifyContent: { xs: 'center', md: 'flex-start' },
              minHeight: 42,
              px: { xs: 1.5, md: 2 },
              textTransform: 'none',
              '&.active': {
                bgcolor: 'transparent',
                color: '#111111',
              },
            }}
          >
            <Box component="span" sx={{ fontSize: 17, fontWeight: 400, lineHeight: 1, width: 18 }}>
              {item.icon}
            </Box>
            {item.label}
          </Button>
        ))}
      </Stack>
    </Paper>
  );
}
