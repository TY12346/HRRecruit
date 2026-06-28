export function candidateFitFromScore(score) {
  if (score === null || score === undefined || score === '') {
    return {
      label: 'Not screened',
      color: 'default',
      description: 'AI screening has not produced a score yet.',
    };
  }

  const numericScore = Number(score);
  if (!Number.isFinite(numericScore)) {
    return {
      label: 'Not screened',
      color: 'default',
      description: 'AI screening has not produced a score yet.',
    };
  }

  if (numericScore >= 85) {
    return {
      label: 'Strong match',
      color: 'success',
      description: 'High scoring candidate. Prioritize recruiter review.',
    };
  }

  if (numericScore >= 70) {
    return {
      label: 'Good match',
      color: 'primary',
      description: 'Promising candidate. Review resume and shortlist context.',
    };
  }

  if (numericScore >= 60) {
    return {
      label: 'Potential match',
      color: 'warning',
      description: 'Borderline candidate. Review missing skills and evidence manually.',
    };
  }

  return {
    label: 'Needs review',
    color: 'default',
    description: 'Lower score. Do not auto-reject; use recruiter judgement.',
  };
}
