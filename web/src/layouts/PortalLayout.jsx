import { Box, Container, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { Link as RouterLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { logout as logoutRequest } from '../api/client.js';
import { useAuthStore } from '../store/authStore.js';
import { NotificationProvider } from '../notifications/NotificationContext.jsx';

const iconProps = {
  fill: 'none',
  height: 22,
  stroke: 'currentColor',
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  strokeWidth: 2,
  viewBox: '0 0 24 24',
  width: 22,
};

function ProfileIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <path d="M10 17l5-5-5-5M15 12H3" />
      <path d="M14 3h4a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3h-4" />
    </svg>
  );
}

const iconProps = {
  fill: 'none',
  height: 22,
  stroke: 'currentColor',
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  strokeWidth: 2,
  viewBox: '0 0 24 24',
  width: 22,
};

function ProfileIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <path d="M10 17l5-5-5-5M15 12H3" />
      <path d="M14 3h4a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3h-4" />
    </svg>
  );
}

export default function PortalLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const clearSession = useAuthStore((state) => state.clearSession);
  const isOnboarding = isAuthenticated && location.pathname.startsWith('/hiring-manager/onboarding/');

  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await logoutRequest(refreshToken);
      }
    } finally {
      clearSession();
      navigate('/login', { replace: true });
    }
  };

  if (isOnboarding) {
    return <Box component="main" sx={{ minHeight: '100vh', p: { xs: 2.5, md: 6 } }}><Outlet /></Box>;
  }

  return (
    <NotificationProvider>
    <Box
      component="main"
      sx={{
        bgcolor: 'background.default',
        minHeight: '100vh',
        pl: { xs: 0, md: isAuthenticated ? '370px' : 0 },
        pt: isAuthenticated ? '64px' : 0,
      }}
    >
      <Box
        component="header"
        sx={{
          alignItems: 'center',
          bgcolor: '#ffffff',
          borderBottom: '1px solid #bfdbfe',
          boxShadow: '0 1px 4px rgba(30, 64, 175, 0.08)',
          display: 'grid',
          columnGap: { xs: 2, md: 4 },
          gridTemplateColumns: { xs: '1fr auto', md: '370px 1fr auto' },
          height: 64,
          left: 0,
          px: { xs: 2, md: 5 },
          position: isAuthenticated ? 'fixed' : 'static',
          right: 0,
          top: 0,
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Typography component="div" sx={{ color: '#1d4ed8', fontSize: 26, fontWeight: 800, letterSpacing: '-0.03em' }}>
          HRRecruit
        </Typography>
        <Typography
          component="div"
          sx={{
            color: '#1e3a8a',
            display: { xs: 'none', md: 'block' },
            fontSize: 14,
            fontWeight: 800,
            pl: 6,
          }}
        >
          {isAuthenticated ? `${user?.role === 'hr_head' ? 'Hiring Manager' : user?.role === 'recruiter' ? 'Recruiter' : 'Interviewer'} Portal` : 'Web Portal'}
        </Typography>

        {isAuthenticated ? (
          <Stack alignItems="center" direction="row" justifyContent="flex-end" spacing={3}>
            <Tooltip title={`Profile: ${user?.full_name ?? user?.email}`}>
              <IconButton aria-label="Profile" component={RouterLink} size="small" sx={{ color: '#1d4ed8' }} to="/profile">
                <ProfileIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Logout">
              <IconButton aria-label="Logout" onClick={handleLogout} size="small" sx={{ color: '#1d4ed8' }}>
                <LogoutIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        ) : null}
      </Box>

      <Container maxWidth={false} sx={{ p: { xs: 2.5, md: 3 } }}>
        <Outlet />
      </Container>
    </Box>
    </NotificationProvider>
  );
}
