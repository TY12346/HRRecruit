import { useEffect, useState } from 'react';
import { Box, Chip, CircularProgress, Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import RecruiterNav from './RecruiterNav.jsx';
import Alert from '../../components/TimedAlert.jsx';
import { getEmployerInvites } from '../../api/client.js';

const label = (value) => value === 'applied' ? 'Applied for job' : value === 'declined' ? 'Declined' : 'No response';
export default function HeadhuntInvitesPage() {
  const [invites, setInvites] = useState([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  useEffect(() => { getEmployerInvites().then(setInvites).catch(() => setError('Unable to load headhunt invites.')).finally(() => setLoading(false)); }, []);
  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}><Typography variant="h5" fontWeight={700}>Headhunt Invites</Typography><Typography color="text.secondary" sx={{ mb: 2 }}>Track employer invitations you have sent to applicants.</Typography>{error && <Alert severity="error">{error}</Alert>}{loading ? <CircularProgress /> : <Table><TableHead><TableRow><TableCell>Applicant</TableCell><TableCell>Job</TableCell><TableCell>Response</TableCell><TableCell>Sent</TableCell></TableRow></TableHead><TableBody>{invites.map((invite) => <TableRow key={invite.id}><TableCell>{invite.applicant_name}<br /><Typography variant="caption">{invite.applicant_email}</Typography></TableCell><TableCell>{invite.job_title}</TableCell><TableCell><Chip size="small" label={label(invite.response)} color={invite.response === 'applied' ? 'success' : invite.response === 'declined' ? 'default' : 'warning'} /></TableCell><TableCell>{new Date(invite.created_at).toLocaleString()}</TableCell></TableRow>)}{!invites.length && <TableRow><TableCell colSpan={4}>No headhunt invites sent yet.</TableCell></TableRow>}</TableBody></Table>}</Paper></Box>;
}
