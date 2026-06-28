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
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getRankedCandidates } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { candidateFitFromScore } from './candidateFit.js';
import { applicationName, getApiErrorMessage, scoreText, titleize } from './recruiterUtils.js';
import {
  APPLICATION_FILTER_DEFAULTS,
  buildApplicationQueryParams,
  deleteApplicationView,
  describeApplicationFilters,
  loadSavedApplicationViews,
  saveApplicationView,
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

function RankingSavedViews({ scope, filters, onApply }) {
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
    if (view) onApply({ ...RANKING_FILTER_DEFAULTS, ...view.filters });
  };

  const removeSavedView = () => {
    if (!selectedView) return;
    setSavedViews(deleteApplicationView(scope, selectedView));
    setSelectedView('');
  };

  return (
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ md: 'center' }}>
      <TextField size="small" label="Saved ranking view" value={viewName} onChange={(event) => setViewName(event.target.value)} />
      <Button variant="outlined" onClick={saveCurrentView} disabled={!viewName.trim()}>Save view</Button>
      <TextField select size="small" label="Apply saved view" value={selectedView} onChange={(event) => applySavedView(event.target.value)} sx={{ minWidth: 220 }}>
        <MenuItem value="">Choose saved view</MenuItem>
        {savedViews.map((view) => <MenuItem key={view.name} value={view.name}>{view.name}</MenuItem>)}
      </TextField>
      <Button color="error" onClick={removeSavedView} disabled={!selectedView}>Delete view</Button>
    </Stack>
  );
}

export default function CandidateRankingPage() {
  const { jobId } = useParams();
  const [candidates, setCandidates] = useState([]);
  const [filters, setFilters] = useState(RANKING_FILTER_DEFAULTS);
  const [draftFilters, setDraftFilters] = useState(RANKING_FILTER_DEFAULTS);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    getRankedCandidates(jobId, buildApplicationQueryParams(filters))
      .then((data) => {
        if (active) setCandidates(data);
      })
      .catch((err) => {
        if (active) setError(getApiErrorMessage(err, 'Unable to load ranked candidates.'));
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

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Qualified candidate ranking</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Real recruitment systems combine ranking with search, fit filters, saved views, and human review before action.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}

        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Stack spacing={2}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
              <TextField fullWidth label="Search qualified candidates, notes, or resume text" value={draftFilters.search} onChange={(event) => setDraftFilters({ ...draftFilters, search: event.target.value })} />
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
            <RankingSavedViews scope={`ranking.${jobId}`} filters={filters} onApply={applyFilters} />
          </Stack>
        </Paper>

        {isLoading ? <CircularProgress /> : null}
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Rank</TableCell>
              <TableCell>Candidate</TableCell>
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
            {candidates.map((candidate, index) => (
              <TableRow key={candidate.id}>
                <TableCell>#{index + 1}</TableCell>
                <TableCell>{applicationName(candidate)}</TableCell>
                <TableCell><Chip label={titleize(candidate.status)} size="small" /></TableCell>
                <TableCell><FitChip score={candidate.final_score} /></TableCell>
                <TableCell>{scoreText(candidate.semantic_score)}</TableCell>
                <TableCell>{scoreText(candidate.skill_score)}</TableCell>
                <TableCell>{scoreText(candidate.experience_score)}</TableCell>
                <TableCell>{scoreText(candidate.education_score)}</TableCell>
                <TableCell><strong>{scoreText(candidate.final_score)}</strong></TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button component={RouterLink} to={`/recruiter/applications/${candidate.id}`} size="small">
                      Profile
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && candidates.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10}>No qualified candidates match the current search or saved ranking view.</TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
