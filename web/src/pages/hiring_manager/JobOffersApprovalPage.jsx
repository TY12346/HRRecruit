import { useEffect, useState } from 'react';
import { Box, Button, Chip, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { approveJobOffer, disapproveJobOffer, getJobOffers } from '../../api/client.js';
import HiringManagerNav from './HiringManagerNav.jsx';
import { applicationName, getApiErrorMessage, titleize } from '../recruiter/recruiterUtils.js';

export default function JobOffersApprovalPage() {
  const [offers, setOffers] = useState([]);
  const [remarks, setRemarks] = useState({});
  const [error, setError] = useState('');
  const load = () => getJobOffers().then(setOffers).catch((err) => setError(getApiErrorMessage(err, 'Unable to load job offers.')));
  useEffect(() => { load(); }, []);
  const review = async (offer, approved) => {
    setError('');
    try {
      if (approved) await approveJobOffer(offer.id, remarks[offer.id] || '');
      else await disapproveJobOffer(offer.id, remarks[offer.id] || '');
      load();
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to review job offer.')); }
  };
  return <Box><HiringManagerNav /><Paper sx={{ p: 3 }}>
    <Typography variant="h5" sx={{ fontWeight: 700 }}>Job offer approvals</Typography>
    <Typography color="text.secondary" sx={{ mb: 2 }}>Review offer terms before recruiters send approved offers to applicants.</Typography>
    {error ? <Alert severity="error">{error}</Alert> : null}
    <Table><TableHead><TableRow><TableCell>Applicant</TableCell><TableCell>Job</TableCell><TableCell>Terms</TableCell><TableCell>Status</TableCell><TableCell>Remarks / reason</TableCell><TableCell>Action</TableCell></TableRow></TableHead>
      <TableBody>{offers.map((offer) => <TableRow key={offer.id}>
        <TableCell>{applicationName(offer.application)}</TableCell><TableCell>{offer.application?.job_title}</TableCell>
        <TableCell>{offer.salary_amount ? `${offer.salary_currency} ${offer.salary_amount}` : 'Salary not specified'}<Typography variant="body2">Start: {offer.start_date || 'TBD'} · {offer.work_arrangement || 'TBD'}</Typography></TableCell>
        <TableCell><Chip size="small" label={offer.offer_status_label || titleize(offer.offer_status)} /></TableCell>
        <TableCell>{offer.offer_status === 'pending_hr_approval' ? <TextField size="small" multiline value={remarks[offer.id] || ''} onChange={(event) => setRemarks((current) => ({ ...current, [offer.id]: event.target.value }))} placeholder="Required when disapproving" /> : offer.hiring_manager_remarks || '—'}</TableCell>
        <TableCell>{offer.offer_status === 'pending_hr_approval' ? <Stack direction="row" spacing={1}><Button onClick={() => review(offer, true)}>Approve</Button><Button color="error" disabled={!remarks[offer.id]?.trim()} onClick={() => review(offer, false)}>Disapprove</Button></Stack> : 'Reviewed'}</TableCell>
      </TableRow>)}</TableBody>
    </Table>
  </Paper></Box>;
}
