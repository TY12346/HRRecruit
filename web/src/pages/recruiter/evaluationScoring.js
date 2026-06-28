export const criterionImportanceOptions = [
  {
    value: 'core',
    label: 'Core competency',
    description: 'Essential interview area. It should strongly affect the final interview score.',
    weight_score: '0.40',
  },
  {
    value: 'standard',
    label: 'Standard competency',
    description: 'Normal interview area. It should meaningfully affect the final score.',
    weight_score: '0.30',
  },
  {
    value: 'supporting',
    label: 'Supporting competency',
    description: 'Useful supporting evidence. It should have moderate influence.',
    weight_score: '0.20',
  },
  {
    value: 'minor',
    label: 'Minor competency',
    description: 'Low-impact area. It should not dominate the final score.',
    weight_score: '0.10',
  },
];

export const blankCriterion = {
  criterion_name: '',
  description: '',
  max_score: '10.00',
  importance_level: 'standard',
  weight_score: '0.30',
};

const normalizeDecimalString = (value, fallback) => {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(2) : fallback;
};

const findClosestImportance = (value) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return criterionImportanceOptions[1];
  }

  return criterionImportanceOptions.reduce((closest, option) => {
    const currentDistance = Math.abs(Number(option.weight_score) - numeric);
    const closestDistance = Math.abs(Number(closest.weight_score) - numeric);
    return currentDistance < closestDistance ? option : closest;
  }, criterionImportanceOptions[1]);
};

export function hydrateCriterion(criterion = {}) {
  const weightScore = normalizeDecimalString(criterion.weight_score, blankCriterion.weight_score);
  const maxScore = normalizeDecimalString(criterion.max_score, blankCriterion.max_score);

  return {
    ...blankCriterion,
    ...criterion,
    max_score: maxScore,
    weight_score: weightScore,
    importance_level: criterion.importance_level ?? findClosestImportance(weightScore).value,
  };
}

export function applyCriterionImportance(criterion, importanceLevel) {
  const option = criterionImportanceOptions.find((item) => item.value === importanceLevel) ?? criterionImportanceOptions[1];
  return {
    ...criterion,
    importance_level: option.value,
    weight_score: option.weight_score,
  };
}

export function cloneCriterion() {
  return { ...blankCriterion };
}

const normalizeWeights = (criteria) => {
  const total = criteria.reduce((sum, criterion) => sum + Number(criterion.weight_score || 0), 0);
  if (!Number.isFinite(total) || total <= 0) {
    return criteria;
  }

  let runningTotal = 0;
  return criteria.map((criterion, index) => {
    if (index === criteria.length - 1) {
      return {
        ...criterion,
        weight_score: Math.max(0, 1 - runningTotal).toFixed(2),
      };
    }

    const normalizedWeight = Math.floor((Number(criterion.weight_score) / total) * 100) / 100;
    runningTotal += normalizedWeight;
    return {
      ...criterion,
      weight_score: normalizedWeight.toFixed(2),
    };
  });
};

export function prepareCriteriaForApi(criteria, { normalizeImportance = true } = {}) {
  const cleaned = criteria.map(({ importance_level, ...criterion }) => criterion);
  return normalizeImportance ? normalizeWeights(cleaned) : cleaned;
}
