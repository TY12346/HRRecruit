import { Box, Container, Typography } from '@mui/material';
import { Outlet } from 'react-router-dom';

export default function PortalLayout() {
  return (
    <Box component="main" sx={{ py: 4 }}>
      <Container maxWidth="lg">
        <Typography component="h1" variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
          HRRecruit Web Portal
        </Typography>
        <Outlet />
      </Container>
    </Box>
  );
}
