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
    <Paper sx={{ p: 1.5, mb: 3 }}>
      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
        {navItems.map((item) => (
          <Button
            component={NavLink}
            end={item.to === '/hr-head'}
            key={item.to}
            to={item.to}
            sx={{
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
