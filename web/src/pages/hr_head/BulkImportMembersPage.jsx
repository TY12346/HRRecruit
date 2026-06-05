import { useState } from 'react';
import { Alert, Box, Button, List, ListItem, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { bulkImportOrganizationMembers } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { getApiErrorMessage } from './hrHeadUtils.js';

export default function BulkImportMembersPage() {
  const [csvFile, setCsvFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!csvFile) {
      setError('Choose a CSV file before importing.');
      return;
    }

    setError('');
    setResult(null);
    setIsSubmitting(true);
    try {
      const data = await bulkImportOrganizationMembers(csvFile);
      setResult(data);
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Unable to import team members.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box>
      <HRHeadNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
          Bulk Import Members
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Upload a UTF-8 CSV file with headers: email, full_name, role, and optional phone_number. Roles must be recruiter or interviewer.
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {result ? (
          <Alert severity={result.errors?.length ? 'warning' : 'success'} sx={{ mb: 2 }}>
            Created {result.created?.length ?? 0} members. {result.errors?.length ?? 0} rows had errors.
          </Alert>
        ) : null}

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <Button component="label" variant="outlined">
              {csvFile ? csvFile.name : 'Choose CSV file'}
              <input hidden accept=".csv,text/csv" type="file" onChange={(event) => setCsvFile(event.target.files?.[0] ?? null)} />
            </Button>
            <Stack direction="row" spacing={1}>
              <Button disabled={isSubmitting} type="submit" variant="contained">
                {isSubmitting ? 'Importing…' : 'Import members'}
              </Button>
              <Button component={RouterLink} to="/hr-head/team" variant="outlined">
                Back to team
              </Button>
            </Stack>
          </Stack>
        </Box>

        {result?.created?.length ? (
          <Box sx={{ mt: 3 }}>
            <Typography component="h3" variant="h6">Created members</Typography>
            <List dense>
              {result.created.map((member) => (
                <ListItem key={member.id}>{member.full_name} — {member.email} ({member.role})</ListItem>
              ))}
            </List>
          </Box>
        ) : null}

        {result?.errors?.length ? (
          <Box sx={{ mt: 3 }}>
            <Typography component="h3" variant="h6">Rows needing attention</Typography>
            <List dense>
              {result.errors.map((rowError) => (
                <ListItem key={rowError.row}>Row {rowError.row}: {JSON.stringify(rowError.errors)}</ListItem>
              ))}
            </List>
          </Box>
        ) : null}
      </Paper>
    </Box>
  );
}
