import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { deactivateOrganizationMember, getOrganizationMembers } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './hrHeadUtils.js';

export default function TeamMembersPage() {
  const [members, setMembers] = useState([]);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [deactivatingId, setDeactivatingId] = useState(null);

  const loadMembers = useCallback(async (searchTerm = search) => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getOrganizationMembers(searchTerm);
      setMembers(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, 'Unable to load team members.'));
    } finally {
      setIsLoading(false);
    }
  }, [search]);

  useEffect(() => {
    let isMounted = true;

    const loadInitialMembers = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getOrganizationMembers('');
        if (isMounted) {
          setMembers(data);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(getApiErrorMessage(loadError, 'Unable to load team members.'));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadInitialMembers();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    loadMembers(search);
  };

  const handleDeactivate = async (member) => {
    const confirmed = window.confirm(`Deactivate ${member.full_name}? They will no longer be able to sign in.`);
    if (!confirmed) {
      return;
    }

    setDeactivatingId(member.id);
    setError('');
    setSuccessMessage('');
    try {
      const response = await deactivateOrganizationMember(member.id);
      setSuccessMessage(response.message ?? 'Team member deactivated successfully.');
      await loadMembers(search);
    } catch (deactivateError) {
      setError(getApiErrorMessage(deactivateError, 'Unable to deactivate team member.'));
    } finally {
      setDeactivatingId(null);
    }
  };

  return (
    <Box>
      <HRHeadNav />
      <Paper sx={{ p: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 3 }}>
          <Box>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }}>
              Team Members
            </Typography>
            <Typography color="text.secondary">
              Search recruiter and interviewer accounts and deactivate access when required.
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button component={RouterLink} to="/hr-head/team/create" variant="contained">
              Create member
            </Button>
            <Button component={RouterLink} to="/hr-head/team/bulk-import" variant="outlined">
              Bulk import
            </Button>
          </Stack>
        </Stack>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {successMessage ? <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert> : null}

        <Box component="form" onSubmit={handleSearchSubmit} sx={{ mb: 2 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <TextField fullWidth label="Search by name, email, or role" onChange={(event) => setSearch(event.target.value)} value={search} />
            <Button type="submit" variant="outlined">
              Search
            </Button>
          </Stack>
        </Box>

        {isLoading ? <CircularProgress aria-label="Loading team members" /> : null}

        <Table sx={{ mt: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Joined</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {members.map((member) => (
              <TableRow key={member.id}>
                <TableCell>{member.full_name}</TableCell>
                <TableCell>{member.email}</TableCell>
                <TableCell>{member.phone_number || '—'}</TableCell>
                <TableCell>{titleize(member.role)}</TableCell>
                <TableCell>
                  <Chip color={member.status === 'active' && member.is_active ? 'success' : 'default'} label={titleize(member.status)} size="small" />
                </TableCell>
                <TableCell>{formatDateTime(member.joined_at)}</TableCell>
                <TableCell align="right">
                  <Button
                    color="error"
                    disabled={member.status !== 'active' || !member.is_active || deactivatingId === member.id}
                    onClick={() => handleDeactivate(member)}
                    size="small"
                    variant="outlined"
                  >
                    {deactivatingId === member.id ? 'Deactivating…' : 'Deactivate'}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && members.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7}>No team members found.</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
