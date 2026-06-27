import { candidateFitFromScore } from './candidateFit.js';

const SCORE_COMPONENT_LABELS = {
  semantic_score: 'Resume-job similarity',
  skill_score: 'Skills match',
  experience_score: 'Experience match',
  education_score: 'Education match',
};

const SCORE_COMPONENT_DESCRIPTIONS = {
  semantic_score: 'How closely the resume text matches the overall job description.',
  skill_score: 'How many required or preferred skills were found in the resume.',
  experience_score: 'Whether the candidate appears to meet the role experience expectation.',
  education_score: 'Whether the detected education level/field matches the job requirement.',
};

const EMPTY_LIST = [];

export function normalizeList(value) {
  if (!value) return EMPTY_LIST;
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  if (typeof value === 'string') return value ? [value] : EMPTY_LIST;
  if (typeof value === 'object') {
    return Object.entries(value)
      .filter(([, nestedValue]) => nestedValue !== null && nestedValue !== undefined && nestedValue !== '' && nestedValue !== false)
      .map(([key, nestedValue]) => `${key}: ${Array.isArray(nestedValue) ? nestedValue.join(', ') : nestedValue}`);
  }
  return [String(value)];
}

export function scoreNumber(value) {
  const numericScore = Number(value);
  return Number.isFinite(numericScore) ? numericScore : null;
}

export function scorePercent(value) {
  const numericScore = scoreNumber(value);
  if (numericScore === null) return 0;
  return Math.max(0, Math.min(100, numericScore));
}

export function buildScoreComponents(scores = {}) {
  return Object.entries(SCORE_COMPONENT_LABELS).map(([key, label]) => ({
    key,
    label,
    description: SCORE_COMPONENT_DESCRIPTIONS[key],
    value: scoreNumber(scores[key]),
    percent: scorePercent(scores[key]),
  }));
}

export function buildScreeningExplainability(profile = {}) {
  const scores = profile.scores ?? {};
  const explanation = scores.explanation ?? profile.score_explanation ?? {};
  const mlScreening = explanation.ml_screening ?? {};
  const finalScore = scoreNumber(scores.final_score ?? explanation.final_score);
  const fit = candidateFitFromScore(finalScore);
  const matchedSkills = normalizeList(explanation.matched_skills ?? explanation.skills?.matched);
  const missingSkills = normalizeList(explanation.missing_skills ?? explanation.skills?.missing);
  const positiveFactors = normalizeList(mlScreening.top_positive_factors ?? explanation.positive_factors);
  const negativeFactors = normalizeList(mlScreening.top_negative_factors ?? explanation.negative_factors);
  const notes = normalizeList(explanation.notes);

  return {
    finalScore,
    fit,
    explanation,
    mlScreening,
    scoreComponents: buildScoreComponents(scores),
    matchedSkills,
    missingSkills,
    positiveFactors,
    negativeFactors,
    notes,
    modelVersion: mlScreening.model_version ?? explanation.model_version ?? 'Rule-based screening',
    fallbackUsed: Boolean(mlScreening.fallback_used ?? explanation.fallback_used),
    confidence: scoreNumber(mlScreening.ml_confidence),
    mlSuitabilityScore: scoreNumber(mlScreening.ml_suitability_score),
    mlMatchLabel: mlScreening.ml_match_label,
    hybridFormula: explanation.hybrid_formula,
  };
}
