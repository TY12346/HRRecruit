export const importanceOptions = [
  {
    value: 'must_have',
    label: 'Must-have',
    description: 'Critical requirement. Strongly affects AI screening and recruiter review priority.',
    weight_score: '0.40',
  },
  {
    value: 'important',
    label: 'Important',
    description: 'Strongly preferred requirement. Meaningfully affects the candidate score.',
    weight_score: '0.30',
  },
  {
    value: 'nice_to_have',
    label: 'Nice-to-have',
    description: 'Bonus requirement. Helps differentiate otherwise similar candidates.',
    weight_score: '0.20',
  },
  {
    value: 'optional',
    label: 'Optional',
    description: 'Low-impact requirement. Useful for notes, but should not filter candidates heavily.',
    weight_score: '0.10',
  },
];


export const blankRequirement = {
  requirement_type: 'skill',
  description: '',
  importance_level: 'important',
  weight_score: '0.30',
  minimum_threshold: '0.60',
};

const normalizeDecimalString = (value, fallback) => {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(2) : fallback;
};

const findClosestOption = (value, options, field) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return options[0];
  }

  return options.reduce((closest, option) => {
    const currentDistance = Math.abs(Number(option[field]) - numeric);
    const closestDistance = Math.abs(Number(closest[field]) - numeric);
    return currentDistance < closestDistance ? option : closest;
  }, options[0]);
};

export function hydrateRequirement(requirement = {}) {
  const weightScore = normalizeDecimalString(requirement.weight_score, blankRequirement.weight_score);
  const minimumThreshold = normalizeDecimalString(requirement.minimum_threshold, blankRequirement.minimum_threshold);

  return {
    ...blankRequirement,
    ...requirement,
    weight_score: weightScore,
    minimum_threshold: minimumThreshold,
    importance_level: requirement.importance_level ?? findClosestOption(weightScore, importanceOptions, 'weight_score').value,
  };
}

export function applyImportance(requirement, importanceLevel) {
  const option = importanceOptions.find((item) => item.value === importanceLevel) ?? importanceOptions[1];
  return {
    ...requirement,
    importance_level: option.value,
    weight_score: option.weight_score,
  };
}


export function cloneRequirement() {
  return { ...blankRequirement };
}

export function prepareRequirementsForApi(requirements) {
  return requirements.map(({ importance_level, ...requirement }) => requirement);
}
