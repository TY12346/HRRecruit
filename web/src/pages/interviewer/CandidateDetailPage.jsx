import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getAssignedInterviews, getCandidateProfile, openApplicationResume } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { formatDateTime, formatExtractedValue, getApiErrorMessage, titleize } from './interviewerUtils.js';

const SCORE_ITEMS = [
  ['semantic_score', 'Semantic match'],
  ['skill_score', 'Skills'],
  ['experience_score', 'Experience'],
  ['education_score', 'Education'],
  ['final_score', 'Final score'],
];

const SCORE_COLOR = {
  strong: 'success',
  good: 'primary',
  moderate: 'warning',
  weak: 'error',
};

const toNumber = (value) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const formatScore = (value) => {
  const numeric = toNumber(value);
  return numeric === null ? '—' : numeric.toFixed(2);
};

const scoreBand = (value) => {
  const numeric = toNumber(value);
  if (numeric === null) return 'weak';
  if (numeric >= 80) return 'strong';
  if (numeric >= 65) return 'good';
  if (numeric >= 50) return 'moderate';
  return 'weak';
};

const asArray = (value) => {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
};

const technicalExplanation = (explanation) => {
  if (!explanation || Object.keys(explanation).length === 0) return 'No technical explanation is available.';
  return JSON.stringify(explanation, null, 2);
};

function ScoreTile({ label, value }) {
  const numeric = toNumber(value);
  const band = scoreBand(value);
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Stack spacing={1}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
            <Typography variant="body2" color="text.secondary">
              {label}
            </Typography>
            <Chip size="small" color={SCORE_COLOR[band]} label={titleize(band)} />
          </Stack>
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            {formatScore(value)}
          </Typography>
          <LinearProgress
            variant="determinate"
            value={numeric === null ? 0 : Math.min(Math.max(numeric, 0), 100)}
            color={SCORE_COLOR[band]}
            sx={{ height: 8, borderRadius: 999 }}
          />
        </Stack>
      </CardContent>
    </Card>
  );
}

function EvidenceChips({ title, values, color = 'default', emptyText = 'None recorded' }) {
  const items = asArray(values).filter(Boolean);
  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 0.75 }}>
        {title}
      </Typography>
      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
        {items.length ? items.map((item) => (
          <Chip key={`${title}-${item}`} size="small" color={color} label={formatExtractedValue(item)} />
        )) : <Typography variant="body2" color="text.secondary">{emptyText}</Typography>}
      </Stack>
    </Box>
  );
}

function AIScoresCard({ scores }) {
  const explanation = scores?.explanation ?? {};
  const mlScreening = explanation.ml_screening ?? {};
  const hasMlScreening = Object.keys(mlScreening).length > 0;
  const notes = explanation.notes ?? explanation.summary ?? '';
  const topPositiveFactors = asArray(mlScreening.top_positive_factors);
  const topNegativeFactors = asArray(mlScreening.top_negative_factors);

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              AI scores
            </Typography>
            <Typography variant="body2" color="text.secondary">
              These scores support interviewer review. They do not replace human judgement.
            </Typography>
          </Box>

          <Grid container spacing={1.5}>
            {SCORE_ITEMS.map(([key, label]) => (
              <Grid item xs={12} sm={6} md={key === 'final_score' ? 12 : 6} key={key}>
                <ScoreTile label={label} value={scores?.[key]} />
              </Grid>
            ))}
          </Grid>

          {notes ? (
            <Alert severity="info" variant="outlined">
              {notes}
            </Alert>
          ) : null}

          <Divider />

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <EvidenceChips title="Matched skills" values={explanation.matched_skills} color="success" />
            </Grid>
            <Grid item xs={12} md={6}>
              <EvidenceChips title="Missing skills" values={explanation.missing_skills} color="warning" />
            </Grid>
          </Grid>

          {hasMlScreening ? (
            <>
              <Divider />
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  ML-assisted screening
                </Typography>
                <Grid container spacing={1.5} sx={{ mt: 0.5 }}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">Suitability score</Typography>
                    <Typography sx={{ fontWeight: 700 }}>{formatScore(mlScreening.ml_suitability_score)}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">Hybrid final score</Typography>
                    <Typography sx={{ fontWeight: 700 }}>{formatScore(mlScreening.hybrid_final_score)}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">Confidence</Typography>
                    <Typography sx={{ fontWeight: 700 }}>{formatScore(mlScreening.confidence)}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">Model version</Typography>
                    <Typography sx={{ fontWeight: 700 }}>{mlScreening.model_version || 'Fallback model'}</Typography>
                  </Grid>
                </Grid>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mt: 1.5 }}>
                  <Chip size="small" label={`Label: ${titleize(mlScreening.ml_match_label)}`} />
                  <Chip
                    size="small"
                    color={mlScreening.fallback_used ? 'warning' : 'success'}
                    label={mlScreening.fallback_used ? 'Fallback used' : 'Trained model used'}
                  />
                </Stack>
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <EvidenceChips title="Top positive factors" values={topPositiveFactors} color="success" />
                </Grid>
                <Grid item xs={12} md={6}>
                  <EvidenceChips title="Top negative factors" values={topNegativeFactors} color="warning" />
                </Grid>
              </Grid>
            </>
          ) : null}

          <Box
            component="details"
            sx={{
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              p: 1.5,
              '& summary': { cursor: 'pointer', fontWeight: 700 },
            }}
          >
            <summary>Show full technical explanation</summary>
            <Box
              component="pre"
              sx={{
                bgcolor: 'grey.50',
                borderRadius: 1,
                mt: 1,
                overflowX: 'auto',
                p: 1.5,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {technicalExplanation(explanation)}
            </Box>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function CandidateDetailPage() {
  const { applicationId } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [interview, setInterview] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCandidateProfile(applicationId), getAssignedInterviews()])
      .then(([profile, interviews]) => {
        setCandidate(profile);
        setInterview(interviews.find((item) => String(item.application?.id) === String(applicationId)) ?? null);
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load candidate detail.')))
      .finally(() => setIsLoading(false));
  }, [applicationId]);

  const applicant = candidate?.applicant_profile ?? {};
  const resume = candidate?.resume_info ?? {};
  const openResume = async () => {
    try {
      await openApplicationResume(applicationId);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to open resume.'));
    }
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          Candidate Detail
        </Typography>
        {error ? <Alert severity="error" sx={{ my: 2 }}>{error}</Alert> : null}
        {isLoading ? <CircularProgress /> : null}
        {candidate ? (
          <Stack spacing={2} sx={{ mt: 2 }}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6">{applicant.full_name}</Typography>
                <Typography color="text.secondary">
                  {applicant.email} • {applicant.phone_number || 'No phone'}
                </Typography>
                <Typography>Application status: {titleize(candidate.status)}</Typography>
                <Typography>Applied: {formatDateTime(candidate.applied_at)}</Typography>
                <Typography>Recruiter remark: {candidate.recruiter_remark || '—'}</Typography>
                {applicant.linkedin_url ? (
                  <Button href={applicant.linkedin_url} target="_blank" rel="noreferrer">
                    LinkedIn
                  </Button>
                ) : null}
                {resume.resume_file ? <Button onClick={openResume}>Open resume</Button> : null}
              </CardContent>
            </Card>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6">Resume extraction</Typography>
                    <Typography><strong>Skills:</strong> {formatExtractedValue(candidate.extracted_skills)}</Typography>
                    <Typography><strong>Experience:</strong> {formatExtractedValue(resume.extracted_experience)}</Typography>
                    <Typography><strong>Education:</strong> {formatExtractedValue(resume.extracted_education)}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <AIScoresCard scores={candidate.scores ?? {}} />
              </Grid>
            </Grid>

            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6">Personal summary</Typography>
                <Typography whiteSpace="pre-line">{applicant.personal_summary || '—'}</Typography>
              </CardContent>
            </Card>

            {interview ? (
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                <Button component={RouterLink} to={`/interviewer/interviews/${interview.id}`} variant="outlined">
                  Open interview
                </Button>
              </Stack>
            ) : null}
          </Stack>
        ) : null}
      </Paper>
    </Box>
  );
}
