import { Badge, Box, Container, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { Link as RouterLink, Outlet, useNavigate } from 'react-router-dom';
import { logout as logoutRequest } from '../api/client.js';
import { useAuthStore } from '../store/authStore.js';

export default function PortalLayout() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const clearSession = useAuthStore((state) => state.clearSession);

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

  return (
    <Box
      component="main"
      sx={{
        bgcolor: '#ffffff',
        minHeight: '100vh',
        pl: { xs: 0, md: isAuthenticated ? '230px' : 0 },
        pt: isAuthenticated ? '64px' : 0,
      }}
    >
      <Box
        component="header"
        sx={{
          alignItems: 'center',
          bgcolor: '#ffffff',
          borderBottom: '1px solid #e5e7eb',
          display: 'grid',
          columnGap: { xs: 2, md: 4 },
          gridTemplateColumns: { xs: '1fr auto', md: '230px 1fr auto' },
          height: 64,
          left: 0,
          px: { xs: 2, md: 5 },
          position: isAuthenticated ? 'fixed' : 'static',
          right: 0,
          top: 0,
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Typography component="div" sx={{ color: '#111111', fontSize: 26, fontWeight: 800, letterSpacing: '-0.03em' }}>
          HRRecruit
        </Typography>
        <Typography
          component="div"
          sx={{
            color: '#111111',
            display: { xs: 'none', md: 'block' },
            fontSize: 14,
            fontWeight: 800,
            pl: 6,
          }}
        >
          {isAuthenticated ? `${user?.role === 'hr_head' ? 'HR Department Head' : user?.role === 'recruiter' ? 'Recruiter' : 'Interviewer'} Portal` : 'Web Portal'}
        </Typography>

        {isAuthenticated ? (
          <Stack alignItems="center" direction="row" justifyContent="flex-end" spacing={3}>
            <Tooltip title="Notifications">
              <IconButton aria-label="Notifications" size="small" sx={{ color: '#111111' }}>
                <Badge color="error" overlap="circular" variant="dot">
                  <Box component="span" sx={{ fontSize: 18, lineHeight: 1 }}>♧</Box>
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title={`Profile: ${user?.full_name ?? user?.email}`}>
              <IconButton aria-label="Profile" component={RouterLink} size="small" sx={{ color: '#111111' }} to="/profile">
                <Box component="span" sx={{ fontSize: 20, lineHeight: 1 }}>●</Box>
              </IconButton>
            </Tooltip>
            <Tooltip title="Logout">
              <IconButton aria-label="Logout" onClick={handleLogout} size="small" sx={{ color: '#111111' }}>
                <Box component="span" sx={{ fontSize: 16, lineHeight: 1 }}>↪</Box>
              </IconButton>
            </Tooltip>
          </Stack>
        ) : null}
      </Box>

      <Container maxWidth={false} sx={{ p: { xs: 2.5, md: 3 } }}>
        <Outlet />
      </Container>
    </Box>
  );
}
