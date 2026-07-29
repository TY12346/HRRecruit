import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useNavigate } from 'react-router-dom';
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

const defaultFilters = {
  search: '',
  skills: '',
  experience: '',
  education: '',
  profile_summary: '',
};

const applicantName = (application) => application?.applicant?.full_name ?? application?.full_name ?? 'Applicant';

const formatExperience = (experiences = []) => experiences.map((experience) => [
  experience.job_title,
  experience.company_name ? `at ${experience.company_name}` : '',
  experience.employment_type,
  experience.location,
].filter(Boolean).join(' ')).join('; ') || '—';

const formatEducation = (educations = []) => educations.map((education) => [
  education.degree_name,
  education.field_of_study ? `in ${education.field_of_study}` : '',
  education.school_name ? `at ${education.school_name}` : '',
].filter(Boolean).join(' ')).join('; ') || '—';

function CollapsibleContent({ children, text, collapseAt = 100 }) {
  const [expanded, setExpanded] = useState(false);
  const shouldCollapse = text.length > collapseAt;

  return (
    <Box sx={{ minWidth: 120, maxWidth: 280 }}>
      <Box sx={!expanded && shouldCollapse ? {
        display: '-webkit-box',
        overflow: 'hidden',
        WebkitBoxOrient: 'vertical',
        WebkitLineClamp: 3,
      } : undefined}>
        {children}
      </Box>
      {shouldCollapse ? (
        <Button size="small" onClick={() => setExpanded((current) => !current)} sx={{ display: 'block', mt: 0.5, p: 0 }}>
          {expanded ? 'Collapse' : 'Expand'}
        </Button>
      ) : null}
    </Box>
  );
}

function getApiErrorMessage(error, fallback) {
  const data = error?.response?.data;
  if (!data) return fallback;
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const firstValue = Object.values(data)[0];
  if (Array.isArray(firstValue)) return firstValue.join(' ');
  return String(firstValue ?? fallback);
}

function buildParams(filters) {
  return Object.fromEntries(
    Object.entries(filters)
      .map(([key, value]) => [key, value.trim()])
      .filter(([, value]) => value),
  );
}

function SearchFilters({ filters, onChange, onApply, onReset }) {
  const update = (key, value) => onChange({ ...filters, [key]: value });
  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Stack spacing={1.5}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <TextField fullWidth label="Search applicant name, email or phone" value={filters.search} onChange={(event) => update('search', event.target.value)} />
          <Button variant="contained" onClick={onApply}>Search</Button>
          <Button variant="outlined" onClick={onReset}>Reset</Button>
        </Stack>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
          <TextField fullWidth label="Skills" value={filters.skills} onChange={(event) => update('skills', event.target.value)} />
          <TextField fullWidth label="Experience" value={filters.experience} onChange={(event) => update('experience', event.target.value)} />
          <TextField fullWidth label="Education" value={filters.education} onChange={(event) => update('education', event.target.value)} />
          <TextField fullWidth label="Profile summary" value={filters.profile_summary} onChange={(event) => update('profile_summary', event.target.value)} />
        </Stack>
      </Stack>
    </Paper>
  );
}

export default function RoleBasedApplicantSearchPage({ role }) {
  const navigate = useNavigate();
  const config = ROLE_CONFIG[role];
  const Nav = config.nav;
  const [filters, setFilters] = useState(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState(defaultFilters);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [inviteApplicant, setInviteApplicant] = useState(null);
  const [profileApplicant, setProfileApplicant] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState('');
  const [isSending, setIsSending] = useState(false);
  const params = useMemo(() => buildParams(appliedFilters), [appliedFilters]);

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
        <SearchFilters filters={filters} onChange={setFilters} onApply={() => setAppliedFilters(filters)} onReset={reset} />
        {isLoading ? <CircularProgress /> : null}
        <TableContainer>
          <Table sx={{ minWidth: 1100 }}>
            <TableHead>
              <TableRow>
                <TableCell>Applicant Name</TableCell>
                <TableCell>Skills</TableCell>
                <TableCell>Experience</TableCell>
                <TableCell>Education</TableCell>
                <TableCell>Profile Summary</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {results.map((application) => {
                const skills = application.skills ?? application.extracted_skills ?? [];
                const experiences = application.experiences ?? [];
                const educations = application.educations ?? [];
                const skillsText = skills.join(', ') || '—';
                const experienceText = formatExperience(experiences);
                const educationText = formatEducation(educations);
                const summaryText = application.personal_summary ?? application.applicant?.personal_summary ?? '—';
                return (
                  <TableRow key={application.id}>
                    <TableCell>{applicantName(application)}</TableCell>
                    <TableCell><CollapsibleContent text={skillsText}>{skillsText}</CollapsibleContent></TableCell>
                    <TableCell><CollapsibleContent text={experienceText}>{experienceText}</CollapsibleContent></TableCell>
                    <TableCell><CollapsibleContent text={educationText}>{educationText}</CollapsibleContent></TableCell>
                    <TableCell><CollapsibleContent text={summaryText}>{summaryText}</CollapsibleContent></TableCell>
                    <TableCell align="right">
                      <Stack spacing={1} sx={{ alignItems: 'flex-end' }}>
                        <Button
                          onClick={() => navigate(role === 'recruiter'
                            ? `/recruiter/applicant-search/${application.id}`
                            : (config.detailBase ? `${config.detailBase}/${application.id}` : '/hiring-manager/hiring-decisions'))}
                          size="small"
                          variant="outlined"
                        >
                          View profile
                        </Button>
                        {role === 'recruiter' ? <Button size="small" variant="contained" onClick={() => setInviteApplicant(application)}>Invite to apply</Button> : null}
                      </Stack>
                    </TableCell>
                  </TableRow>
                );
              })}
              {!isLoading && results.length === 0 ? (
                <TableRow><TableCell colSpan={6}>No applicants match the current search.</TableCell></TableRow>
              ) : null}
            </TableBody>
          </Table>
        </TableContainer>
        <Dialog open={Boolean(inviteApplicant)} onClose={() => !isSending && setInviteApplicant(null)} fullWidth>
          <DialogTitle>Invite {inviteApplicant?.full_name} to apply</DialogTitle>
          <DialogContent>
            <TextField
              select
              fullWidth
              sx={{ mt: 1 }}
              label="Open job"
              value={selectedJob}
              onChange={(event) => setSelectedJob(event.target.value)}
              SelectProps={{ native: true }}
            >
              <option value="" />
              {jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}
            </TextField>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setInviteApplicant(null)} disabled={isSending}>Cancel</Button>
            <Button variant="contained" onClick={sendInvite} disabled={!selectedJob || isSending}>
              {isSending ? 'Sending…' : 'Send invite'}
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Box>
  );
}
