import { useEffect, useMemo, useState } from 'react';
import {

  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
import { Link as RouterLink } from 'react-router-dom';
import { getApplicantSearch, getJobs, sendEmployerInvite } from '../../api/client.js';
import HiringManagerNav from '../hiring_manager/HiringManagerNav.jsx';
import InterviewerNav from '../interviewer/InterviewerNav.jsx';
import RecruiterNav from '../recruiter/RecruiterNav.jsx';

const ROLE_CONFIG = {
  recruiter: {
    title: 'Applicant Search & Shortlisting',
    description: 'Search all active applicant profiles, then invite a candidate to apply for one of your open jobs.',
    nav: RecruiterNav,
    detailBase: '/recruiter/applications',
  },
  interviewer: {
    title: 'My Interview Applicants',
    description: 'Search only applicants and interviews assigned to you. Organization-wide applicants are not exposed.',
    nav: InterviewerNav,
    detailBase: '/interviewer/applicants',
  },
  hr_head: {
    title: 'Organization Applicant Search',
    description: 'Search applicants across your organization for oversight, approvals, and hiring pipeline review.',
    nav: HiringManagerNav,
  },
};

const STATUS_OPTIONS = [
  ['all', 'All application statuses'],
  ['under_review', 'Under review'],
  ['rejected', 'Rejected'],
];

const INTERVIEW_OPTIONS = [
  ['all', 'All interview statuses'],
  ['upcoming', 'Upcoming interviews'],
  ['completed', 'Completed interviews'],
  ['pending_evaluation', 'Pending evaluation'],
  ['invited', 'Invited'],
  ['scheduled', 'Scheduled'],
  ['cancelled', 'Cancelled'],
];

const SORT_OPTIONS = [
  ['newest', 'Newest first'],
  ['oldest', 'Oldest first'],
  ['score_desc', 'Highest AI score'],
  ['score_asc', 'Lowest AI score'],
  ['applicant_az', 'Applicant A-Z'],
];

const defaultFilters = {
  search: '',
  status: 'all',
  skills: '',
  education: '',
  experience: '',
  min_score: '',
  max_score: '',
  date_from: '',
  date_to: '',
  interviewer_status: 'all',
  department: '',
  recruiter_id: '',
  pending_approval: 'all',
  final_decision: '',
  sort: 'newest',
};

const titleize = (value) => String(value ?? '—').replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
const formatDate = (value) => (value ? new Date(value).toLocaleString() : '—');
const applicantName = (application) => application?.applicant?.full_name ?? application?.full_name ?? 'Applicant';
const applicantEmail = (application) => application?.applicant?.email ?? application?.email ?? '—';
const scoreText = (score) => (score === null || score === undefined || score === '' ? '—' : Number(score).toFixed(2));

function getApiErrorMessage(error, fallback) {
  const data = error?.response?.data;
  if (!data) return fallback;
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const firstValue = Object.values(data)[0];
  if (Array.isArray(firstValue)) return firstValue.join(' ');
  return String(firstValue ?? fallback);
}

function buildParams(filters, role) {
  const params = {};
  for (const [key, value] of Object.entries(filters)) {
    if (value === '' || value === 'all') continue;
    if (role === 'interviewer' && ['skills', 'education', 'experience', 'min_score', 'max_score', 'department', 'recruiter_id', 'pending_approval', 'final_decision'].includes(key)) continue;
    if (role === 'recruiter' && ['department', 'recruiter_id', 'pending_approval', 'final_decision'].includes(key)) continue;
    params[key] = value;
  }
  return params;
}

function SearchFilters({ role, filters, onChange, onApply, onReset }) {
  const update = (key, value) => onChange({ ...filters, [key]: value });
  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Stack spacing={2}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
          <TextField fullWidth label="Search applicant, email, job, remark, resume" value={filters.search} onChange={(event) => update('search', event.target.value)} />
          <TextField select label="Application status" value={filters.status} onChange={(event) => update('status', event.target.value)} sx={{ minWidth: 210 }}>
            {STATUS_OPTIONS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </TextField>
          <TextField select label="Sort" value={filters.sort} onChange={(event) => update('sort', event.target.value)} sx={{ minWidth: 180 }}>
            {SORT_OPTIONS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </TextField>
        </Stack>
        {role !== 'interviewer' ? (
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
            <TextField label="Skills" value={filters.skills} onChange={(event) => update('skills', event.target.value)} />
            <TextField label="Education" value={filters.education} onChange={(event) => update('education', event.target.value)} />
            <TextField label="Experience" value={filters.experience} onChange={(event) => update('experience', event.target.value)} />
            <TextField label="Min AI score" type="number" value={filters.min_score} onChange={(event) => update('min_score', event.target.value)} />
            <TextField label="Max AI score" type="number" value={filters.max_score} onChange={(event) => update('max_score', event.target.value)} />
          </Stack>
        ) : null}
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
          <TextField select label="Interview" value={filters.interviewer_status} onChange={(event) => update('interviewer_status', event.target.value)} sx={{ minWidth: 210 }}>
            {INTERVIEW_OPTIONS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </TextField>
          <TextField label="Date from" type="date" value={filters.date_from} onChange={(event) => update('date_from', event.target.value)} InputLabelProps={{ shrink: true }} />
          <TextField label="Date to" type="date" value={filters.date_to} onChange={(event) => update('date_to', event.target.value)} InputLabelProps={{ shrink: true }} />
          {role === 'hr_head' ? <TextField label="Department" value={filters.department} onChange={(event) => update('department', event.target.value)} /> : null}
          {role === 'hr_head' ? <TextField label="Recruiter ID" value={filters.recruiter_id} onChange={(event) => update('recruiter_id', event.target.value)} /> : null}
          {role === 'hr_head' ? (
            <TextField select label="Pending approval" value={filters.pending_approval} onChange={(event) => update('pending_approval', event.target.value)} sx={{ minWidth: 180 }}>
              <MenuItem value="all">Any</MenuItem>
              <MenuItem value="true">Pending approval</MenuItem>
              <MenuItem value="false">Not pending</MenuItem>
            </TextField>
          ) : null}
        </Stack>
        {role === 'hr_head' ? <TextField label="Final decision/status" value={filters.final_decision} onChange={(event) => update('final_decision', event.target.value)} helperText="Examples: hire, reject, approved, rejected, pending_hr_approval" /> : null}
        <Stack direction="row" spacing={1}>
          <Button variant="contained" onClick={onApply}>Search</Button>
          <Button variant="outlined" onClick={onReset}>Reset</Button>
        </Stack>
      </Stack>
    </Paper>
  );
}

export default function RoleBasedApplicantSearchPage({ role }) {
  const config = ROLE_CONFIG[role];
  const Nav = config.nav;
  const [filters, setFilters] = useState(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState(defaultFilters);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [inviteApplicant, setInviteApplicant] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState('');
  const [isSending, setIsSending] = useState(false);
  const params = useMemo(() => buildParams(appliedFilters, role), [appliedFilters, role]);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError('');
    getApplicantSearch(params)
      .then((data) => { if (active) setResults(data); })
      .catch((err) => { if (active) setError(getApiErrorMessage(err, 'Unable to search applicants.')); })
      .finally(() => { if (active) setIsLoading(false); });
    return () => { active = false; };
  }, [params]);

  useEffect(() => { if (role === 'recruiter') getJobs().then((data) => setJobs(data.filter((job) => job.status === 'open'))).catch(() => {}); }, [role]);

  const sendInvite = async () => {
    if (!selectedJob || !inviteApplicant) return;
    setIsSending(true);
    try { await sendEmployerInvite({ applicant_id: inviteApplicant.id, job_id: selectedJob }); setInviteApplicant(null); setSelectedJob(''); }
    catch (err) { setError(getApiErrorMessage(err, 'Unable to send employer invite.')); }
    finally { setIsSending(false); }
  };

  const reset = () => {
    setFilters(defaultFilters);
    setAppliedFilters(defaultFilters);
  };

  return (
    <Box>
      <Nav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>{config.title}</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>{config.description}</Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        <SearchFilters role={role} filters={filters} onChange={setFilters} onApply={() => setAppliedFilters(filters)} onReset={reset} />
        {isLoading ? <CircularProgress /> : null}
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Applicant</TableCell>
              <TableCell>Email</TableCell>
              {role !== 'recruiter' ? <TableCell>Job</TableCell> : <TableCell>Skills</TableCell>}
              {role !== 'recruiter' ? <TableCell>Status</TableCell> : <TableCell>Profile summary</TableCell>}
              {role !== 'recruiter' ? <TableCell>AI score</TableCell> : null}
              {role !== 'recruiter' ? <TableCell>Interview</TableCell> : null}
              {role === 'hr_head' ? <TableCell>Recruiter</TableCell> : null}
              <TableCell>Applied</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.map((application) => (
              <TableRow key={application.id}>
                <TableCell>{applicantName(application)}</TableCell>
                <TableCell>{applicantEmail(application)}</TableCell>
                {role !== 'recruiter' ? <TableCell>{application.job_title}</TableCell> : <TableCell>{(application.skills || []).join(', ') || '—'}</TableCell>}
                {role !== 'recruiter' ? <TableCell><Chip label={titleize(application.status)} size="small" /></TableCell> : <TableCell>{application.personal_summary || '—'}</TableCell>}
                {role !== 'recruiter' ? <TableCell>{scoreText(application.final_score)}</TableCell> : null}
                {role !== 'recruiter' ? <TableCell>{application.latest_interview ? `${titleize(application.latest_interview.status)} • ${formatDate(application.latest_interview.scheduled_datetime)}` : '—'}</TableCell> : null}
                {role === 'hr_head' ? <TableCell>{application.recruiter?.full_name ?? '—'}</TableCell> : null}
                {role !== 'recruiter' ? <TableCell>{formatDate(application.applied_at)}</TableCell> : null}
                <TableCell align="right">
                  {role === 'recruiter' ? <Button size="small" variant="contained" onClick={() => setInviteApplicant(application)}>Invite to apply</Button> : (config.detailBase ? <Button component={RouterLink} to={`${config.detailBase}/${application.id}`} size="small">Open</Button> : <Button component={RouterLink} to="/hiring-manager/hiring-decisions" size="small">Approvals</Button>)}
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && results.length === 0 ? (
              <TableRow><TableCell colSpan={role === 'hr_head' ? 9 : 8}>No applicants match the current search.</TableCell></TableRow>
            ) : null}
          </TableBody>
        </Table>
        <Dialog open={Boolean(inviteApplicant)} onClose={() => !isSending && setInviteApplicant(null)} fullWidth><DialogTitle>Invite {inviteApplicant?.full_name} to apply</DialogTitle><DialogContent><TextField select fullWidth sx={{ mt: 1 }} label="Open job" value={selectedJob} onChange={(event) => setSelectedJob(event.target.value)}>{jobs.map((job) => <MenuItem key={job.id} value={job.id}>{job.title}</MenuItem>)}</TextField></DialogContent><DialogActions><Button onClick={() => setInviteApplicant(null)} disabled={isSending}>Cancel</Button><Button variant="contained" onClick={sendInvite} disabled={!selectedJob || isSending}>{isSending ? 'Sending…' : 'Send invite'}</Button></DialogActions></Dialog>
      </Paper>
    </Box>
  );
}
