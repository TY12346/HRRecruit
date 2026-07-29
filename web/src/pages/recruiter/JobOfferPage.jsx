import { useCallback, useEffect, useState } from 'react';
import {

  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
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
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useParams, useSearchParams } from 'react-router-dom';
import { getApplications, getJob, getJobHiringDecisions, getJobOffers, getJobs, resubmitJobOffer, sendApprovedJobOffer, sendJobOffer, withdrawJobOffer } from '../../api/client.js';
import ApplicantJobSummary from '../../components/ApplicantJobSummary.jsx';
import RecruiterNav from './RecruiterNav.jsx';
import { applicationName, formatDate, formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';
import { getCommunicationTemplates, renderApplicationTemplate } from './communicationTemplates.js';

const offerNextStep = (offer) => {
  if (offer.offer_status === 'pending_hr_approval') return 'Wait for the hiring manager to review the offer.';
  if (offer.offer_status === 'approved_by_hr') return 'Send the approved offer to the applicant.';
  if (offer.offer_status === 'disapproved_by_hr') return 'Review the feedback, edit the offer, and resubmit it.';
  if (offer.offer_status === 'pending_applicant_response') return 'Wait for the applicant response.';
  if (offer.offer_status === 'accepted_by_applicant') return 'No further action is required; the vacancy has been updated.';
  if (offer.offer_status === 'rejected_by_applicant') return 'The vacancy remains open; make another hiring decision if needed.';
  return 'Complete the offer terms and submit them for approval.';
};

const approvedOfferApplications = (apps, decisions) => {
  const approvedIds = new Set(
    decisions
      .filter((decision) => decision.status === 'approved' && decision.decision_type === 'recommend_hire')
      .flatMap((decision) => decision.items.map((item) => item.application.id)),
  );
  return apps.filter((app) => app.status === 'under_review' && approvedIds.has(app.id));
};

function JobSpecificOffers({ jobId }) {
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
  const [editingOfferId, setEditingOfferId] = useState(null);

  const load = async () => {
    setIsLoading(true);
    try {
      const params = jobId ? { job_id: jobId } : {};
      const [apps, jobOffers, decisions] = await Promise.all([
        getApplications(params),
        getJobOffers(jobId ? { job_posting: jobId } : {}),
        getJobHiringDecisions(jobId ? { job_posting: jobId } : {}),
      ]);
      const approvedApps = approvedOfferApplications(apps, decisions);
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
    const params = jobId ? { job_id: jobId } : {};
    Promise.all([
      getApplications(params),
      getJobOffers(jobId ? { job_posting: jobId } : {}),
      getJobHiringDecisions(jobId ? { job_posting: jobId } : {}),
    ])
      .then(([apps, jobOffers, decisions]) => {
        if (!active) return;
        const approvedApps = approvedOfferApplications(apps, decisions);
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
  }, [jobId]);

  const offerTemplates = getCommunicationTemplates('offer');
  const selectedApplication = applications.find((app) => String(app.id) === String(applicationId));
  const [job, setJob] = useState(null);
  useEffect(() => { getJob(jobId).then(setJob).catch(() => {}); }, [jobId]);
  const jobTitle = job?.title || selectedApplication?.job_title || offers[0]?.application?.job_title;

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
      const payload = {
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
      };
      if (editingOfferId) await resubmitJobOffer(editingOfferId, payload);
      else await sendJobOffer(applicationId, payload);
      setSuccess(editingOfferId ? 'Revised job offer resubmitted for hiring manager approval.' : 'Job offer submitted for hiring manager approval.');
      setEditingOfferId(null);
      load();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to send job offer.'));
    }
  };

  const editOffer = (offer) => {
    setEditingOfferId(offer.id);
    setApplicationId(String(offer.application.id));
    setMessage(offer.offer_message);
    setDeadline(formatDate(new Date(offer.respond_deadline)));
    setSalaryAmount(offer.salary_amount || '');
    setSalaryCurrency(offer.salary_currency || 'MYR');
    setStartDate(offer.start_date || '');
    setEmploymentType(offer.employment_type || '');
    setWorkArrangement(offer.work_arrangement || '');
    setProbationMonths(offer.probation_months ?? '');
    setBenefitsSummary(offer.benefits_summary || '');
    setInternalNotes(offer.internal_notes || '');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const sendToApplicant = async (offerId) => {
    setError('');
    try {
      await sendApprovedJobOffer(offerId);
      setSuccess('Approved offer sent to the applicant.');
      load();
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to send offer to applicant.')); }
  };


  const withdrawOffer = async (offerId) => {
    setError('');
    setSuccess('');
    try {
      await withdrawJobOffer(offerId, { internal_notes: 'Withdrawn from recruiter offer management page.' });
      setSuccess('Job offer withdrawn. You can send a revised offer if the applicant remains HR-approved.');
      load();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to withdraw job offer.'));
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>{jobId ? 'Create job offer' : 'Job offers'}</Typography>
        {jobId ? <Typography color="text.secondary" sx={{ mb: 2 }}>
          {jobTitle ? `${jobTitle} — ` : ''}Draft an offer and track every offer related to this job.
        </Typography> : null}
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}><Button component={RouterLink} to={`/recruiter/jobs/${jobId}`}>Back to job</Button><Button component={RouterLink} to="/recruiter/job-offers">View offers across all jobs</Button></Stack>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        {isLoading ? <CircularProgress /> : (
          <Stack spacing={3}>
            <Box component="form" onSubmit={submit}>
              <Stack spacing={2}>
                <TextField label="HR-approved applicant" select required disabled={Boolean(editingOfferId)} value={applicationId} onChange={(e) => setApplicationId(e.target.value)}>
                  {applications.map((app) => <MenuItem key={app.id} value={app.id}><ApplicantJobSummary applicantName={applicationName(app)} jobTitle={app.job_title} variant="body2" /></MenuItem>)}
                </TextField>
                <TextField
                  label="Applicant communication template"
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
                <Button disabled={!applicationId} type="submit" variant="contained">{editingOfferId ? 'Save changes and resubmit for approval' : 'Submit job offer for approval'}</Button>
              </Stack>
            </Box>

            <Typography variant="h6">Job offers</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Applicant</TableCell>
                  <TableCell>Job</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Hiring manager feedback</TableCell>
                  <TableCell>Compensation</TableCell>
                  <TableCell>Start / work</TableCell>
                  <TableCell>Deadline</TableCell>
                  <TableCell>Submitted / sent</TableCell>
                  <TableCell>Next step</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {offers.map((offer) => (
                  <TableRow key={offer.id}>
                    <TableCell>{applicationName(offer.application)}</TableCell>
                    <TableCell>{offer.application?.job_title}</TableCell>
                    <TableCell><Chip label={offer.offer_status_label || titleize(offer.offer_status)} size="small" /></TableCell>
                    <TableCell>{offer.hiring_manager_remarks || '—'}</TableCell>
                    <TableCell>{offer.salary_amount ? `${offer.salary_currency} ${offer.salary_amount}` : 'Not specified'}</TableCell>
                    <TableCell>{offer.start_date || 'TBD'} / {offer.work_arrangement || 'TBD'}</TableCell>
                    <TableCell>{formatDateTime(offer.respond_deadline)}</TableCell>
                    <TableCell>{formatDateTime(offer.sent_at)}</TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>{offerNextStep(offer)}</Typography>
                      {offer.offer_status === 'approved_by_hr' ? <Button onClick={() => sendToApplicant(offer.id)} size="small">Send to applicant</Button> : null}
                      {offer.offer_status === 'disapproved_by_hr' ? <Button onClick={() => editOffer(offer)} size="small">Edit and resubmit</Button> : null}
                      {offer.offer_status === 'pending_applicant_response' ? <Button color="warning" onClick={() => withdrawOffer(offer.id)} size="small">Withdraw</Button> : null}
                    </TableCell>
                  </TableRow>
                ))}
                {!offers.length ? <TableRow><TableCell colSpan={9}>{jobId ? 'No job offers have been created for this job yet.' : 'No job offers have been created yet.'}</TableCell></TableRow> : null}
              </TableBody>
            </Table>
          </Stack>
        )}
      </Paper>
    </Box>
  );
}

const offerStatuses = ['drafting', 'pending_hr_approval', 'approved_by_hr', 'disapproved_by_hr', 'pending_applicant_response', 'accepted_by_applicant', 'rejected_by_applicant'];
function GlobalOffers() {
  const [params, setParams] = useSearchParams(); const keys = ['search','job_id','offer_status','deadline','date_from','date_to']; const filters = Object.fromEntries(keys.map(k => [k, params.get(k) || '']));
  const [offers,setOffers]=useState([]); const [jobs,setJobs]=useState([]); const [error,setError]=useState(''); const [success,setSuccess]=useState(''); const [loading,setLoading]=useState(true);
  const load=useCallback(async()=>{setLoading(true);setError('');try{const query=Object.fromEntries(Object.entries(filters).filter(([,v])=>v));if(query.job_id){query.job_posting=query.job_id;delete query.job_id;}const [records,owned]=await Promise.all([getJobOffers(query),getJobs()]);setOffers(records);setJobs(owned);}catch(e){setError(getApiErrorMessage(e,'Unable to load job offers.'));}finally{setLoading(false);}
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[params.toString()]); useEffect(()=>{load();},[load]);
  const update=(key,value)=>{const next=new URLSearchParams(params);value?next.set(key,value):next.delete(key);setParams(next);};
  const act=async(action,id,message)=>{setError('');if(action==='withdraw'&&!window.confirm('Withdraw this offer from applicant consideration?'))return;try{if(action==='send')await sendApprovedJobOffer(id);else await withdrawJobOffer(id,{internal_notes:'Withdrawn from recruiter cross-job offer queue.'});setSuccess(message);load();}catch(e){setError(getApiErrorMessage(e,'Unable to update the offer.'));}};
  const cards={'Pending Hiring Manager approval':'pending_hr_approval','Approved and ready to send':'approved_by_hr','Disapproved and requiring revision':'disapproved_by_hr','Awaiting applicant response':'pending_applicant_response','Accepted':'accepted_by_applicant','Declined':'rejected_by_applicant'};
  return <Box><RecruiterNav/><Paper sx={{p:{xs:2,md:3}}}><Typography component="h1" variant="h5" fontWeight={700}>Offers across all jobs</Typography><Typography color="text.secondary">Manage the offer lifecycle across all jobs you manage.</Typography>{error?<Alert severity="error" action={<Button color="inherit" onClick={load}>Retry</Button>}>{error}</Alert>:null}{success?<Alert severity="success">{success}</Alert>:null}
    <Grid container spacing={2} sx={{my:2}}>{Object.entries(cards).map(([label,status])=><Grid item xs={12} sm={6} md={4} key={status}><Card variant="outlined"><CardContent><Typography color="text.secondary">{label}</Typography><Typography variant="h4">{offers.filter(o=>o.offer_status===status).length}</Typography></CardContent></Card></Grid>)}</Grid>
    <Stack direction={{xs:'column',md:'row'}} spacing={1} useFlexGap flexWrap="wrap"><TextField size="small" label="Search" value={filters.search} onChange={e=>update('search',e.target.value)}/><TextField select size="small" label="Job" value={filters.job_id} onChange={e=>update('job_id',e.target.value)} sx={{minWidth:180}}><MenuItem value="">All jobs</MenuItem>{jobs.map(j=><MenuItem key={j.id} value={j.id}>{j.title}</MenuItem>)}</TextField><TextField select size="small" label="Offer status" value={filters.offer_status} onChange={e=>update('offer_status',e.target.value)} sx={{minWidth:200}}><MenuItem value="">All statuses</MenuItem>{offerStatuses.map(v=><MenuItem key={v} value={v}>{titleize(v)}</MenuItem>)}</TextField><TextField select size="small" label="Response deadline" value={filters.deadline} onChange={e=>update('deadline',e.target.value)} sx={{minWidth:180}}><MenuItem value="">All</MenuItem><MenuItem value="due_soon">Due soon</MenuItem><MenuItem value="overdue">Overdue</MenuItem></TextField>{['date_from','date_to'].map(k=><TextField key={k} size="small" type="date" label={k==='date_from'?'Date from':'Date to'} slotProps={{inputLabel:{shrink:true}}} value={filters[k]} onChange={e=>update(k,e.target.value)} sx={{minWidth:185}}/>)}{params.toString()?<Button onClick={()=>setParams({})}>Reset filters</Button>:null}</Stack>
    {loading?<CircularProgress aria-label="Loading job offers" sx={{mt:3}}/>:<Box sx={{overflowX:'auto'}}><Table sx={{mt:2,minWidth:1350}}><TableHead><TableRow>{['Applicant','Job','Compensation','Start date','Work arrangement','Status','Hiring Manager feedback','Response deadline','Last relevant timestamp','Next step','Actions'].map(h=><TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead><TableBody>{offers.map(o=><TableRow key={o.id}><TableCell>{applicationName(o.application)}</TableCell><TableCell>{o.application?.job_title}</TableCell><TableCell>{o.salary_amount?`${o.salary_currency} ${o.salary_amount}`:'Not specified'}</TableCell><TableCell>{o.start_date||'TBD'}</TableCell><TableCell>{o.work_arrangement||'TBD'}</TableCell><TableCell><Chip size="small" label={o.offer_status_label||titleize(o.offer_status)}/></TableCell><TableCell>{o.hiring_manager_remarks||'—'}</TableCell><TableCell>{formatDateTime(o.respond_deadline)}</TableCell><TableCell>{formatDateTime(o.responded_at||o.reviewed_at||o.sent_at)}</TableCell><TableCell>{offerNextStep(o)}</TableCell><TableCell><Stack>{o.offer_status==='approved_by_hr'?<Button onClick={()=>act('send',o.id,'Approved offer sent to the applicant.')}>Send approved offer</Button>:null}{o.offer_status==='disapproved_by_hr'?<Button component={RouterLink} to={`/recruiter/jobs/${o.application?.job}/job-offers`}>Edit and resubmit</Button>:null}{o.offer_status==='pending_applicant_response'?<Button color="warning" onClick={()=>act('withdraw',o.id,'Offer withdrawn.')}>Withdraw offer</Button>:null}{o.offer_status==='rejected_by_applicant'?<Button component={RouterLink} to={`/recruiter/jobs/${o.application?.job}/hiring-decision`}>Review hiring decision</Button>:null}<Button component={RouterLink} to={`/recruiter/jobs/${o.application?.job}`}>View job</Button></Stack></TableCell></TableRow>)}{!offers.length?<TableRow><TableCell colSpan={11}>No offers match the current filters.</TableCell></TableRow>:null}</TableBody></Table></Box>}
  </Paper></Box>;
}

export default function JobOfferPage() { const { jobId } = useParams(); return jobId ? <JobSpecificOffers jobId={jobId}/> : <GlobalOffers/>; }
