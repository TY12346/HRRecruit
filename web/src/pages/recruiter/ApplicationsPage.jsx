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
  Tooltip,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { getApplications, rejectApplication } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { candidateFitFromScore } from './candidateFit.js';
import { applicationName, formatDateTime, getApiErrorMessage, scoreText, titleize } from './recruiterUtils.js';
import { renderApplicationTemplate } from './communicationTemplates.js';
import {
  APPLICATION_FILTER_DEFAULTS,
  buildApplicationQueryParams,
  deleteApplicationView,
  describeApplicationFilters,
  loadSavedApplicationViews,
  saveApplicationView,
} from './applicationSearchViews.js';

const STATUS_FILTERS = [
  ['all', 'All statuses'],
  ['submitted', 'Submitted'],
  ['screened_qualified', 'Screened qualified'],
  ['screened_not_qualified', 'Screened not qualified'],
  ['shortlisted', 'Shortlisted'],
  ['interview_invited', 'Interview invited'],
  ['interview_accepted', 'Interview accepted'],
  ['evaluation_submitted', 'Evaluation submitted'],
  ['decision_pending', 'Decision pending'],
  ['offer_sent', 'Offer sent'],
  ['hired', 'Hired'],
  ['rejected', 'Rejected'],
];

const FIT_FILTERS = [
  ['all', 'All AI fit'],
  ['strong', 'Strong fit (75+)'],
  ['possible', 'Possible fit (50-74)'],
  ['low', 'Low fit (<50)'],
];

const SORT_OPTIONS = [
  ['newest', 'Newest first'],
  ['oldest', 'Oldest first'],
  ['score_desc', 'Highest score'],
  ['score_asc', 'Lowest score'],
  ['candidate_az', 'Candidate A-Z'],
];

function FitChip({ score }) {
  const fit = candidateFitFromScore(score);
  return (
    <Tooltip title={fit.description}>
      <Chip color={fit.color} label={fit.label} size="small" />
    </Tooltip>
  );
}

function SavedViewsToolbar({ scope, filters, onApply }) {
  const [savedViews, setSavedViews] = useState(() => loadSavedApplicationViews(scope));
  const [viewName, setViewName] = useState('');
  const [selectedView, setSelectedView] = useState('');

  const saveCurrentView = () => {
    const nextViews = saveApplicationView(scope, viewName, filters);
    setSavedViews(nextViews);
    setSelectedView(viewName.trim());
    setViewName('');
  };

  const applySavedView = (name) => {
    setSelectedView(name);
    const view = savedViews.find((item) => item.name === name);
    if (view) onApply(view.filters);
  };

  const removeSavedView = () => {
    if (!selectedView) return;
    setSavedViews(deleteApplicationView(scope, selectedView));
    setSelectedView('');
  };

  return (
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ md: 'center' }}>
      <TextField size="small" label="Saved view name" value={viewName} onChange={(event) => setViewName(event.target.value)} />
      <Button variant="outlined" onClick={saveCurrentView} disabled={!viewName.trim()}>Save view</Button>
      <TextField select size="small" label="Apply saved view" value={selectedView} onChange={(event) => applySavedView(event.target.value)} sx={{ minWidth: 220 }}>
        <MenuItem value="">Choose saved view</MenuItem>
        {savedViews.map((view) => <MenuItem key={view.name} value={view.name}>{view.name}</MenuItem>)}
      </TextField>
      <Button color="error" onClick={removeSavedView} disabled={!selectedView}>Delete view</Button>
    </Stack>
  );
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [filters, setFilters] = useState(APPLICATION_FILTER_DEFAULTS);
  const [draftFilters, setDraftFilters] = useState(APPLICATION_FILTER_DEFAULTS);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const load = async (nextFilters = filters) => {
    setIsLoading(true);
    try {
      setApplications(await getApplications(buildApplicationQueryParams(nextFilters)));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load applications.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    getApplications(buildApplicationQueryParams(filters))
      .then((data) => {
        if (active) setApplications(data);
      })
      .catch((err) => {
        if (active) setError(getApiErrorMessage(err, 'Unable to load applications.'));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [filters]);

  const applyFilters = (nextFilters = draftFilters) => {
    const normalized = { ...APPLICATION_FILTER_DEFAULTS, ...nextFilters };
    setDraftFilters(normalized);
    setFilters(normalized);
  };

  const resetFilters = () => applyFilters(APPLICATION_FILTER_DEFAULTS);

  const reject = async (app) => {
    const defaultMessage = renderApplicationTemplate('rejection', app.status === 'evaluation_submitted' ? 'rejection_after_interview' : 'rejection_general', app);
    const reason = window.prompt('Candidate rejection message', defaultMessage);
    if (!reason) return;
    setBusyId(app.id);
    try {
      await rejectApplication(app.id, { reason, remark: reason });
      setSuccess('Candidate rejected.');
      load(filters);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to reject candidate.'));
    } finally {
      setBusyId(null);
    }
  };

  const activeFilterLabels = describeApplicationFilters(filters);

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Applications</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Search, filter, sort, and save repeatable recruiter views. AI fit labels remain decision support only.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}

        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Stack spacing={2}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
              <TextField fullWidth label="Search candidates, jobs, notes, or resume text" value={draftFilters.search} onChange={(event) => setDraftFilters({ ...draftFilters, search: event.target.value })} />
              <TextField select label="Status" value={draftFilters.status} onChange={(event) => setDraftFilters({ ...draftFilters, status: event.target.value })} sx={{ minWidth: 190 }}>
                {STATUS_FILTERS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
              </TextField>
              <TextField select label="AI fit" value={draftFilters.fit} onChange={(event) => setDraftFilters({ ...draftFilters, fit: event.target.value })} sx={{ minWidth: 180 }}>
                {FIT_FILTERS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
              </TextField>
              <TextField select label="Sort" value={draftFilters.sort} onChange={(event) => setDraftFilters({ ...draftFilters, sort: event.target.value })} sx={{ minWidth: 170 }}>
                {SORT_OPTIONS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
              </TextField>
            </Stack>
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              <Button variant="contained" onClick={() => applyFilters()}>Apply filters</Button>
              <Button variant="outlined" onClick={resetFilters}>Reset</Button>
              {activeFilterLabels.length ? activeFilterLabels.map((label) => <Chip key={label} label={titleize(label)} size="small" />) : <Chip label="Default view" size="small" />}
            </Stack>
            <SavedViewsToolbar scope="applications" filters={filters} onApply={applyFilters} />
          </Stack>
        </Paper>

        {isLoading ? <CircularProgress /> : null}
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Candidate</TableCell>
              <TableCell>Job</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>AI fit</TableCell>
              <TableCell>Final score</TableCell>
              <TableCell>Applied</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {applications.map((app) => (
              <TableRow key={app.id}>
                <TableCell>{applicationName(app)}</TableCell>
                <TableCell>{app.job_title}</TableCell>
                <TableCell><Chip label={titleize(app.status)} size="small" /></TableCell>
                <TableCell><FitChip score={app.final_score} /></TableCell>
                <TableCell>{scoreText(app.final_score)}</TableCell>
                <TableCell>{formatDateTime(app.applied_at)}</TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button component={RouterLink} to={`/recruiter/applications/${app.id}`} size="small">Profile</Button>
                    {app.status !== 'rejected' ? (
                      <Button component={RouterLink} to={`/recruiter/applications/${app.id}/assign-interview`} size="small">
                        Assign
                      </Button>
                    ) : null}
                    {app.status !== 'rejected' ? (
                      <Button color="error" disabled={busyId === app.id} onClick={() => reject(app)} size="small">
                        Reject
                      </Button>
                    ) : null}
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && applications.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7}>No applications match the current search or saved view.</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
