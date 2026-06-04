import { Alert, Paper, Typography } from '@mui/material';

export default function LoginPage() {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography component="h2" variant="h5" sx={{ mb: 2 }}>
        Staff Login
      </Typography>
      <Alert severity="info">
        Authentication screens will be implemented in a later task for recruiters,
        interviewers, and HR department heads.
      </Alert>
    </Paper>
  );
}
