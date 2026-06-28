import { Component } from 'react';
import { Alert, Box, Button, Paper, Stack, Typography } from '@mui/material';

export default class AppErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    // Keep the app from becoming a white page while preserving console diagnostics for developers.
    // eslint-disable-next-line no-console
    console.error('HRRecruit web app render failure', error, errorInfo);
  }

  render() {
    const { error } = this.state;
    const { children } = this.props;

    if (!error) {
      return children;
    }

    return (
      <Box sx={{ p: 3 }}>
        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography component="h1" variant="h5" sx={{ fontWeight: 700 }}>
              HRRecruit could not render this page
            </Typography>
            <Alert severity="error">
              {error?.message || 'An unexpected browser error occurred while loading the web app.'}
            </Alert>
            <Typography color="text.secondary" variant="body2">
              Refresh the page. If this happens after deployment, check that the built assets are served from the same base path as the router.
            </Typography>
            <Button variant="contained" onClick={() => window.location.assign(import.meta.env.BASE_URL || '/')}>
              Reload HRRecruit
            </Button>
          </Stack>
        </Paper>
      </Box>
    );
  }
}
