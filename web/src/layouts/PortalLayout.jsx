import { Box, Button, Container, Stack, Typography } from '@mui/material';
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
    <Box component="main" sx={{ py: 4 }}>
      <Container maxWidth="lg">
        <Stack
          alignItems={{ xs: 'flex-start', sm: 'center' }}
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          spacing={2}
          sx={{ mb: 3 }}
        >
          <Box>
            <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>
              HRRecruit Web Portal
            </Typography>
            {isAuthenticated ? (
              <Typography color="text.secondary">
                Signed in as {user?.full_name ?? user?.email} ({user?.role})
              </Typography>
            ) : null}
          </Box>

          {isAuthenticated ? (
            <Stack direction="row" spacing={1}>
              <Button component={RouterLink} to="/profile" variant="outlined">
                Profile
              </Button>
              <Button color="secondary" onClick={handleLogout} variant="contained">
                Logout
              </Button>
            </Stack>
          ) : null}
        </Stack>
        <Outlet />
      </Container>
    </Box>
  );
}
