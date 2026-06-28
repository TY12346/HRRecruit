import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  MenuItem,
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
import { getApplications, getJobOffers, sendJobOffer, withdrawJobOffer } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { applicationName, formatDate, formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';
import { getCommunicationTemplates, renderApplicationTemplate } from './communicationTemplates.js';

export default function JobOfferPage() {
  const [applications, setApplications] = useState([]);
  const [offers, setOffers] = useState([]);
  const [applicationId, setApplicationId] = useState('');
  const [templateId, setTemplateId] = useState('offer_standard');
  const [message, setMessage] = useState('Congratulations. HR has approved your hiring decision and we would like to extend this job offer.');
  const [deadline, setDeadline] = useState(() => formatDate(new Date(Date.now() + 7 * 86400000)));
  const [salaryAmount, setSalaryAmount] = useState('');
  const [salaryCurrency, setSalaryCurrency] = useState('MYR');
  const [startDate, setStartDate] = useState('');
  const [employmentType, setEmploymentType] = useState('Full-time');
  const [workArrangement, setWorkArrangement] = useState('Hybrid');
  const [probationMonths, setProbationMonths] = useState('6');
  const [benefitsSummary, setBenefitsSummary] = useState('');
  const [internalNotes, setInternalNotes] = useState('');
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    setIsLoading(true);
    try {
      const [apps, jobOffers] = await Promise.all([getApplications(), getJobOffers()]);
      const approvedApps = apps.filter((app) => app.status === 'hr_approved');
      setApplications(approvedApps);
      setOffers(jobOffers);
      if (!applicationId && approvedApps[0]) setApplicationId(String(approvedApps[0].id));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load offer data.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    Promise.all([getApplications(), getJobOffers()])
      .then(([apps, jobOffers]) => {
        if (!active) return;
        const approvedApps = apps.filter((app) => app.status === 'hr_approved');
        setApplications(approvedApps);
        setOffers(jobOffers);
        if (approvedApps[0]) setApplicationId(String(approvedApps[0].id));
      })
      .catch((err) => {
        if (active) setError(getApiErrorMessage(err, 'Unable to load offer data.'));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => { active = false; };
  }, []);

  const offerTemplates = getCommunicationTemplates('offer');
  const selectedApplication = applications.find((app) => String(app.id) === String(applicationId));

  const applyTemplate = (selectedTemplateId = templateId) => {
    const renderedDeadline = deadline ? formatDateTime(new Date(deadline).toISOString()) : 'the response deadline';
    setTemplateId(selectedTemplateId);
    setMessage(renderApplicationTemplate('offer', selectedTemplateId, selectedApplication ?? {}, { deadline: renderedDeadline }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    try {
      await sendJobOffer(applicationId, {
        offer_message: message,
        respond_deadline: new Date(deadline).toISOString(),
        salary_amount: salaryAmount || undefined,
        salary_currency: salaryCurrency,
        start_date: startDate || undefined,
        employment_type: employmentType,
        work_arrangement: workArrangement,
        probation_months: probationMonths || undefined,
        benefits_summary: benefitsSummary,
        internal_notes: internalNotes,
        offer_letter_file: file,
      });
      setSuccess('Job offer sent with compensation and start-date details.');
      load();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to send job offer.'));
    }
  };


  const withdrawOffer = async (offerId) => {
    setError('');
    setSuccess('');
    try {
      await withdrawJobOffer(offerId, { internal_notes: 'Withdrawn from recruiter offer management page.' });
      setSuccess('Job offer withdrawn. You can send a revised offer if the candidate remains HR-approved.');
      load();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to withdraw job offer.'));
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Job offers</Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        {isLoading ? <CircularProgress /> : (
          <Stack spacing={3}>
            <Box component="form" onSubmit={submit}>
              <Stack spacing={2}>
                <TextField label="HR-approved candidate" select required value={applicationId} onChange={(e) => setApplicationId(e.target.value)}>
                  {applications.map((app) => <MenuItem key={app.id} value={app.id}>{applicationName(app)} — {app.job_title}</MenuItem>)}
                </TextField>
                <TextField
                  label="Candidate communication template"
                  select
                  value={templateId}
                  onChange={(e) => applyTemplate(e.target.value)}
                  helperText="Choose a reusable offer style, then edit the message before sending."
                >
                  {offerTemplates.map((template) => <MenuItem key={template.id} value={template.id}>{template.label} — {template.tone}</MenuItem>)}
                </TextField>
                <Button type="button" variant="outlined" onClick={() => applyTemplate()}>Apply template</Button>
                <TextField label="Offer message" required multiline minRows={4} value={message} onChange={(e) => setMessage(e.target.value)} />
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                  <TextField label="Salary amount" type="number" value={salaryAmount} onChange={(e) => setSalaryAmount(e.target.value)} helperText="Optional but recommended for realistic offers." />
                  <TextField label="Currency" value={salaryCurrency} onChange={(e) => setSalaryCurrency(e.target.value.toUpperCase())} inputProps={{ maxLength: 3 }} />
                  <TextField label="Start date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} InputLabelProps={{ shrink: true }} />
                </Stack>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                  <TextField label="Employment type" value={employmentType} onChange={(e) => setEmploymentType(e.target.value)} />
                  <TextField label="Work arrangement" select value={workArrangement} onChange={(e) => setWorkArrangement(e.target.value)}>
                    {['On-site', 'Hybrid', 'Remote'].map((option) => <MenuItem key={option} value={option}>{option}</MenuItem>)}
                  </TextField>
                  <TextField label="Probation months" type="number" value={probationMonths} onChange={(e) => setProbationMonths(e.target.value)} />
                </Stack>
                <TextField label="Benefits summary" multiline minRows={2} value={benefitsSummary} onChange={(e) => setBenefitsSummary(e.target.value)} placeholder="Medical, leave, bonus, learning allowance…" />
                <TextField label="Internal offer notes" multiline minRows={2} value={internalNotes} onChange={(e) => setInternalNotes(e.target.value)} helperText="Visible to recruiter/HR users only; use this for negotiation context or approval notes." />
                <TextField label="Response deadline" type="datetime-local" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
                <input accept=".pdf,.doc,.docx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} type="file" />
                <Button disabled={!applicationId} type="submit" variant="contained">Send job offer</Button>
              </Stack>
            </Box>

            <Typography variant="h6">Sent offers</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Candidate</TableCell>
                  <TableCell>Job</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Compensation</TableCell>
                  <TableCell>Start / work</TableCell>
                  <TableCell>Deadline</TableCell>
                  <TableCell>Sent</TableCell>
                  <TableCell>Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {offers.map((offer) => (
                  <TableRow key={offer.id}>
                    <TableCell>{applicationName(offer.application)}</TableCell>
                    <TableCell>{offer.application?.job_title}</TableCell>
                    <TableCell><Chip label={titleize(offer.offer_status)} size="small" /></TableCell>
                    <TableCell>{offer.salary_amount ? `${offer.salary_currency} ${offer.salary_amount}` : 'Not specified'}</TableCell>
                    <TableCell>{offer.start_date || 'TBD'} / {offer.work_arrangement || 'TBD'}</TableCell>
                    <TableCell>{formatDateTime(offer.respond_deadline)}</TableCell>
                    <TableCell>{formatDateTime(offer.sent_at)}</TableCell>
                    <TableCell>{offer.offer_status === 'sent' ? <Button color="warning" onClick={() => withdrawOffer(offer.id)} size="small">Withdraw</Button> : null}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Stack>
        )}
      </Paper>
    </Box>
  );
}
