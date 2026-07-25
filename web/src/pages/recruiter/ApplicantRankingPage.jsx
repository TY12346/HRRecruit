import { useEffect, useState } from 'react';
import {
  Autocomplete,
  Box,
  Button,
  Checkbox,
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
  Tooltip,
  Typography,
} from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { assignInterviewer, getOrganizationMembers, getRankedApplicants, rejectApplication } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { applicantFitFromScore } from './applicantFit.js';
import { applicationName, getApiErrorMessage, scoreText, titleize } from './recruiterUtils.js';
import {
  APPLICATION_FILTER_DEFAULTS,
  buildApplicationQueryParams,
  describeApplicationFilters,
} from './applicationSearchViews.js';

const RANKING_FILTER_DEFAULTS = {
  ...APPLICATION_FILTER_DEFAULTS,
  status: 'all',
  sort: 'score_desc',
};

const FIT_FILTERS = [
  ['all', 'All AI fit'],
  ['strong', 'Strong fit (75+)'],
  ['possible', 'Possible fit (50-74)'],
  ['low', 'Low fit (<50)'],
];

const SORT_OPTIONS = [
  ['score_desc', 'Highest score'],
  ['score_asc', 'Lowest score'],
  ['newest', 'Newest applied'],
  ['oldest', 'Oldest applied'],
  ['applicant_az', 'Applicant A-Z'],
];

function FitChip({ score }) {
  const fit = applicantFitFromScore(score);
  return (
    <Tooltip title={fit.description}>
      <Chip color={fit.color} label={fit.label} size="small" />
    </Tooltip>
  );
}

export default function ApplicantRankingPage() {
  const { jobId } = useParams();
  const [applicants, setApplicants] = useState([]);
  const [filters, setFilters] = useState(RANKING_FILTER_DEFAULTS);
  const [draftFilters, setDraftFilters] = useState(RANKING_FILTER_DEFAULTS);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState([]);
  const [interviewers, setInterviewers] = useState([]);
  const [selectedInterviewerIds, setSelectedInterviewerIds] = useState([]);
  const [assigningIds, setAssigningIds] = useState([]);
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    getRankedApplicants(jobId, buildApplicationQueryParams(filters))
      .then((data) => {
        if (active) {
          setApplicants(data);
          setSelectedIds((current) => current.filter((id) => data.some((applicant) => applicant.id === id && applicant.status !== 'rejected' && !applicant.assigned_interviewer)));
        }
      })
      .catch((err) => {
        if (active) setError(getApiErrorMessage(err, 'Unable to load ranked applicants.'));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [jobId, filters]);

  const applyFilters = (nextFilters = draftFilters) => {
    const normalized = { ...RANKING_FILTER_DEFAULTS, ...nextFilters, status: 'all' };
    setDraftFilters(normalized);
    setFilters(normalized);
  };

  const resetFilters = () => applyFilters(RANKING_FILTER_DEFAULTS);
  const activeFilterLabels = describeApplicationFilters(filters).filter((label) => !label.startsWith('Status:'));
  const actionableApplicants = applicants.filter((applicant) => applicant.status !== 'rejected' && !applicant.assigned_interviewer);
  const allSelected = actionableApplicants.length > 0 && actionableApplicants.every((applicant) => selectedIds.includes(applicant.id));
  const toggleAll = () => setSelectedIds(allSelected ? [] : actionableApplicants.map((applicant) => applicant.id));
  const toggleOne = (id) => setSelectedIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);

  const openAssignment = async (ids) => {
    setError('');
    setAssigningIds(ids);
    try {
      const members = await getOrganizationMembers('');
      setInterviewers(members.filter((member) => member.role === 'interviewer' && member.status === 'active' && member.user_id));
    } catch (err) {
      setAssigningIds([]);
      setError(getApiErrorMessage(err, 'Unable to load interviewers.'));
    }
  };

  const assignSelected = async () => {
    setIsBusy(true);
    try {
      await Promise.all(assigningIds.map((id) => assignInterviewer(id, { interviewer_ids: selectedInterviewerIds.map(Number) })));
      setApplicants((current) => current.map((applicant) => (
        assigningIds.includes(applicant.id)
          ? { ...applicant, assigned_interviewer: { id: Number(selectedInterviewerIds[0]) } }
          : applicant
      )));
      setSuccess(`Interviewer assigned to ${assigningIds.length} applicant${assigningIds.length === 1 ? '' : 's'}.`);
      setSelectedIds((current) => current.filter((id) => !assigningIds.includes(id)));
      setAssigningIds([]);
      setSelectedInterviewerIds([]);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to assign interviewer.'));
    } finally {
      setIsBusy(false);
    }
  };

  const rejectSelected = async (ids) => {
    const reason = window.prompt(`Rejection reason for ${ids.length} applicant${ids.length === 1 ? '' : 's'}`);
    if (!reason) return;
    setIsBusy(true);
    try {
      await Promise.all(ids.map((id) => rejectApplication(id, { reason, remark: reason })));
      setApplicants((current) => current.filter((applicant) => !ids.includes(applicant.id)));
      setSelectedIds((current) => current.filter((id) => !ids.includes(id)));
      setSuccess(`${ids.length} applicant${ids.length === 1 ? '' : 's'} rejected.`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to reject applicant.'));
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Qualified applicant ranking</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Compare qualified applicants using ranking, search, and AI fit filters before taking action.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}

        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Stack spacing={2}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
              <TextField fullWidth label="Search qualified applicants, notes, or resume text" value={draftFilters.search} onChange={(event) => setDraftFilters({ ...draftFilters, search: event.target.value })} />
              <TextField select label="AI fit" value={draftFilters.fit} onChange={(event) => setDraftFilters({ ...draftFilters, fit: event.target.value })} sx={{ minWidth: 180 }}>
                {FIT_FILTERS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
              </TextField>
              <TextField select label="Sort" value={draftFilters.sort} onChange={(event) => setDraftFilters({ ...draftFilters, sort: event.target.value })} sx={{ minWidth: 180 }}>
                {SORT_OPTIONS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
              </TextField>
            </Stack>
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              <Button variant="contained" onClick={() => applyFilters()}>Apply ranking filters</Button>
              <Button variant="outlined" onClick={resetFilters}>Reset</Button>
              {activeFilterLabels.length ? activeFilterLabels.map((label) => <Chip key={label} label={titleize(label)} size="small" />) : <Chip label="Default ranking" size="small" />}
            </Stack>
          </Stack>
        </Paper>

        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Button variant="contained" disabled={!selectedIds.length || isBusy} onClick={() => openAssignment(selectedIds)}>Assign interviewer</Button>
          <Button variant="outlined" color="error" disabled={!selectedIds.length || isBusy} onClick={() => rejectSelected(selectedIds)}>Reject selected</Button>
          {selectedIds.length ? <Typography color="text.secondary" sx={{ alignSelf: 'center' }}>{selectedIds.length} selected</Typography> : null}
        </Stack>

        {isLoading ? <CircularProgress /> : null}
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox"><Checkbox checked={allSelected} indeterminate={selectedIds.length > 0 && !allSelected} disabled={!actionableApplicants.length} onChange={toggleAll} inputProps={{ 'aria-label': 'Select all actionable applicants' }} /></TableCell>
              <TableCell>Rank</TableCell>
              <TableCell>Applicant</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>AI fit</TableCell>
              <TableCell>Semantic</TableCell>
              <TableCell>Skill</TableCell>
              <TableCell>Experience</TableCell>
              <TableCell>Education</TableCell>
              <TableCell>Final</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {applicants.map((applicant, index) => (
              <TableRow key={applicant.id}>
                <TableCell padding="checkbox"><Checkbox checked={selectedIds.includes(applicant.id)} disabled={applicant.status === 'rejected' || Boolean(applicant.assigned_interviewer)} onChange={() => toggleOne(applicant.id)} inputProps={{ 'aria-label': `Select ${applicationName(applicant)}` }} /></TableCell>
                <TableCell>#{index + 1}</TableCell>
                <TableCell>{applicationName(applicant)}</TableCell>
                <TableCell><Chip label={titleize(applicant.status)} size="small" /></TableCell>
                <TableCell><FitChip score={applicant.final_score} /></TableCell>
                <TableCell>{scoreText(applicant.semantic_score)}</TableCell>
                <TableCell>{scoreText(applicant.skill_score)}</TableCell>
                <TableCell>{scoreText(applicant.experience_score)}</TableCell>
                <TableCell>{scoreText(applicant.education_score)}</TableCell>
                <TableCell><strong>{scoreText(applicant.final_score)}</strong></TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button component={RouterLink} to={`/recruiter/applications/${applicant.id}`} size="small">View</Button>
                    {applicant.status !== 'rejected' && !applicant.assigned_interviewer ? (
                      <>
                        <Button size="small" disabled={isBusy} onClick={() => openAssignment([applicant.id])}>Assign interviewer</Button>
                        <Button size="small" color="error" disabled={isBusy} onClick={() => rejectSelected([applicant.id])}>Reject</Button>
                      </>
                    ) : null}
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && applicants.length === 0 ? (
              <TableRow>
                <TableCell colSpan={11}>No qualified applicants match the current search.</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
      <Dialog open={assigningIds.length > 0} onClose={() => !isBusy && setAssigningIds([])} fullWidth maxWidth="sm">
        <DialogTitle>Assign interviewer</DialogTitle>
        <DialogContent>
          <Autocomplete
            multiple
            disableCloseOnSelect
            options={interviewers}
            value={interviewers.filter((interviewer) => selectedInterviewerIds.includes(interviewer.user_id))}
            getOptionDisabled={(option) => selectedInterviewerIds.length >= 3 && !selectedInterviewerIds.includes(option.user_id)}
            isOptionEqualToValue={(option, value) => option.user_id === value.user_id}
            getOptionLabel={(option) => `${option.full_name} (${option.email})`}
            onChange={(_, selected) => setSelectedInterviewerIds(selected.slice(0, 3).map((interviewer) => interviewer.user_id))}
            renderInput={(params) => <TextField {...params} margin="dense" label="Interviewers" helperText="Select up to 3 interviewers." />}
          />
          {!interviewers.length ? <Typography color="text.secondary">No active interviewers are available.</Typography> : null}
        </DialogContent>
        <DialogActions>
          <Button disabled={isBusy} onClick={() => setAssigningIds([])}>Cancel</Button>
          <Button variant="contained" disabled={!selectedInterviewerIds.length || isBusy} onClick={assignSelected}>{isBusy ? 'Assigning…' : `Assign panel to ${assigningIds.length}`}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
