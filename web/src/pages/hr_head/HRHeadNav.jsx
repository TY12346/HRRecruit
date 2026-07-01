import { Button, Paper, Stack } from '@mui/material';
import { NavLink } from 'react-router-dom';

const navItems = [
  { label: 'Dashboard', to: '/hr-head' },
  { label: 'Organization', to: '/hr-head/organization' },
  { label: 'Team', to: '/hr-head/team' },
  { label: 'Hiring Decisions', to: '/hr-head/hiring-decisions' },
  { label: 'Billing', to: '/hr-head/billing' },
  { label: 'Analytics', to: '/hr-head/analytics' },
  { label: 'Notifications', to: '/hr-head/notifications' },
];

export default function HRHeadNav() {
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
        {navItems.map((item) => (
          <Button
            component={NavLink}
            end={item.to === '/hr-head'}
            key={item.to}
            to={item.to}
            sx={{
              justifyContent: { md: 'flex-start' },
              '&.active': {
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
              },
            }}
          >
            {item.label}
          </Button>
        ))}
      </Stack>
    </Paper>
  );
}
