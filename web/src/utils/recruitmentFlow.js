export const APPLICATION_PHASES = [
  { key: 'applied', label: 'Applied', statuses: ['applied'] },
  { key: 'shortlisted', label: 'Shortlisted', statuses: ['shortlisted'] },
  { key: 'rejected', label: 'Rejected', statuses: ['rejected'] },
];

const STATUS_DETAILS = {
  applied: {
    label: 'Applied',
    description: 'The application was received and is being reviewed.',
    nextActions: {
      recruiter: 'Review the AI screening evidence, then shortlist or reject the applicant.',
      applicant: 'Wait for the recruitment team to review your application.',
    },
  },
  shortlisted: {
    label: 'Shortlisted',
    description: 'The recruiter selected the applicant to continue in the recruitment process.',
    nextActions: {
      recruiter: 'Arrange and monitor the applicant interviews.',
      interviewer: 'Review your interview assignment and complete the interview evaluation.',
      applicant: 'Watch for interview invitations and offer updates.',
    },
  },
  rejected: {
    label: 'Rejected',
    description: 'The application is no longer moving forward.',
    nextActions: {
      recruiter: 'No further application action is required.',
      applicant: 'You may apply for other open roles.',
    },
  },
};

export function getApplicationStatusInfo(status, role = 'recruiter') {
  const detail = STATUS_DETAILS[status] ?? {
    label: status ? status.replaceAll('_', ' ') : 'Unknown status',
    description: 'This application status needs review.',
    nextActions: {},
  };
  return {
    ...detail,
    nextAction: detail.nextActions?.[role] ?? detail.nextActions?.recruiter ?? 'Review the application details.',
  };
}

export function getApplicationPhaseIndex(status) {
  const index = APPLICATION_PHASES.findIndex((phase) => phase.statuses.includes(status));
  return index >= 0 ? index : 0;
}
