export const APPLICATION_PHASES = [
  { key: 'applied', label: 'Applied', statuses: ['submitted', 'screened'] },
  { key: 'screening', label: 'Screening', statuses: ['screened_qualified', 'screened_not_qualified'] },
  { key: 'shortlist', label: 'Shortlist', statuses: ['shortlisted', 'interview_invited'] },
  { key: 'interview', label: 'Interview', statuses: ['interview_accepted', 'interview_declined', 'interviewing'] },
  { key: 'evaluation', label: 'Evaluation', statuses: ['evaluation_submitted'] },
  { key: 'hr_review', label: 'HR review', statuses: ['decision_pending', 'hr_approved', 'hr_rejected'] },
  { key: 'offer', label: 'Offer', statuses: ['offer_sent', 'offer_accepted', 'offer_declined'] },
  { key: 'hired', label: 'Hired', statuses: ['hired'] },
];

const STATUS_DETAILS = {
  submitted: {
    label: 'Applied',
    description: 'The application was received and is ready for resume screening.',
    nextActions: {
      recruiter: 'Review AI screening evidence, then shortlist or reject the candidate.',
      applicant: 'Your application was submitted. Wait for the recruitment team to review it.',
    },
  },
  screened: {
    label: 'Screening in progress',
    description: 'Resume screening has started but the next recruiting action is not complete yet.',
    nextActions: {
      recruiter: 'Check the screening result when available, then decide whether to shortlist.',
      applicant: 'Your resume is being reviewed.',
    },
  },
  screened_qualified: {
    label: 'Passed screening',
    description: 'AI-assisted screening suggests this candidate may be a fit. A recruiter still makes the decision.',
    nextActions: {
      recruiter: 'Shortlist and assign an interviewer, or reject with a clear reason.',
      applicant: 'Your application passed the screening stage. Wait for interview scheduling updates.',
    },
  },
  screened_not_qualified: {
    label: 'Needs recruiter review',
    description: 'Screening found gaps against the job requirements, but this is not a final hiring decision.',
    nextActions: {
      recruiter: 'Review the evidence manually before deciding whether to shortlist or reject.',
      applicant: 'The recruitment team is reviewing your application details.',
    },
  },
  shortlisted: {
    label: 'Shortlisted',
    description: 'The recruiter selected the candidate for the interview stage.',
    nextActions: {
      recruiter: 'Create an interview scheduling request so the applicant can pick a slot.',
      interviewer: 'Wait for the interview slot to be scheduled, then prepare for the interview.',
      applicant: 'Watch for an invitation to choose an interview slot.',
    },
  },
  interview_invited: {
    label: 'Interview invitation sent',
    description: 'The candidate has been invited to schedule or confirm an interview.',
    nextActions: {
      recruiter: 'Wait for the applicant to pick an available interview slot.',
      applicant: 'Choose a suitable interview slot from your interview invitations.',
    },
  },
  interview_accepted: {
    label: 'Interview scheduled',
    description: 'The applicant selected a slot and the interview is scheduled.',
    nextActions: {
      recruiter: 'Wait for the interviewer to complete the interview and submit an evaluation.',
      interviewer: 'Conduct the interview, then upload notes/recording and submit the evaluation.',
      applicant: 'Attend the interview at the scheduled time.',
    },
  },
  interview_declined: {
    label: 'Interview declined',
    description: 'The interview invitation or slot was declined.',
    nextActions: {
      recruiter: 'Decide whether to arrange another scheduling request or reject the application.',
      applicant: 'Contact the recruiter if you need help with interview scheduling.',
    },
  },
  interviewing: {
    label: 'Interview in progress',
    description: 'The candidate is currently in the interview stage.',
    nextActions: {
      interviewer: 'Complete the interview evaluation after the interview.',
      recruiter: 'Wait for the interviewer evaluation.',
    },
  },
  evaluation_submitted: {
    label: 'Evaluation submitted',
    description: 'The interviewer submitted the structured evaluation for recruiter review.',
    nextActions: {
      recruiter: 'Submit a hire or reject recommendation for HR approval.',
      interviewer: 'No further action is needed unless the recruiter asks for clarification.',
      applicant: 'Wait for the hiring decision review.',
    },
  },
  decision_pending: {
    label: 'Waiting for HR approval',
    description: 'The recruiter submitted a recommendation and HR must approve or reject it.',
    nextActions: {
      recruiter: 'Wait for the HR department head to review the recommendation.',
      hr_head: 'Review the recruiter recommendation and approve or reject it.',
      applicant: 'Your application is in final internal review.',
    },
  },
  hr_approved: {
    label: 'Approved for offer',
    description: 'HR approved the hire recommendation. The candidate is ready for an offer.',
    nextActions: {
      recruiter: 'Prepare and send the job offer.',
      hr_head: 'Wait for the recruiter to send the offer and for the applicant response.',
      applicant: 'Wait for the official job offer.',
    },
  },
  hr_rejected: {
    label: 'HR did not approve recommendation',
    description: 'HR rejected the recruiter recommendation. This is an internal review outcome.',
    nextActions: {
      recruiter: 'Review HR feedback and decide the appropriate follow-up.',
      hr_head: 'No further action is needed unless the recruiter resubmits or follows up.',
    },
  },
  offer_sent: {
    label: 'Offer sent',
    description: 'A job offer has been sent to the applicant.',
    nextActions: {
      recruiter: 'Wait for the applicant to accept or decline the offer.',
      hr_head: 'Monitor offer response progress.',
      applicant: 'Review the offer and accept or decline it before the deadline.',
    },
  },
  offer_accepted: {
    label: 'Offer accepted',
    description: 'The applicant accepted the offer. Hiring completion is being finalized.',
    nextActions: {
      recruiter: 'Confirm the final hiring record and any handoff steps.',
      applicant: 'Wait for next steps from the organization.',
    },
  },
  offer_declined: {
    label: 'Offer declined',
    description: 'The applicant declined the job offer.',
    nextActions: {
      recruiter: 'Close the application or decide whether to follow up.',
      applicant: 'No further action is required.',
    },
  },
  hired: {
    label: 'Hired',
    description: 'The candidate accepted the offer and the recruitment flow is complete.',
    nextActions: {
      recruiter: 'Recruitment is complete for this application.',
      hr_head: 'Recruitment is complete for this application.',
      applicant: 'Congratulations — you have been hired.',
    },
  },
  rejected: {
    label: 'Not selected',
    description: 'The application is no longer moving forward.',
    nextActions: {
      recruiter: 'No further action is required unless the rejection was made in error.',
      applicant: 'This application is closed. You may apply for other open roles.',
    },
  },
  withdrawn: {
    label: 'Withdrawn',
    description: 'The applicant withdrew the application.',
    nextActions: {
      recruiter: 'No further action is required.',
      applicant: 'This application has been withdrawn.',
    },
  },
};

export function getApplicationStatusInfo(status, role = 'recruiter') {
  const detail = STATUS_DETAILS[status] ?? {
    label: status ? status.replaceAll('_', ' ') : 'Unknown status',
    description: 'This application is in a recruitment stage that needs review.',
    nextActions: {},
  };
  return {
    ...detail,
    nextAction: detail.nextActions?.[role] ?? detail.nextActions?.recruiter ?? 'Review the application details for the next available action.',
  };
}

export function getApplicationPhaseIndex(status) {
  const index = APPLICATION_PHASES.findIndex((phase) => phase.statuses.includes(status));
  return index >= 0 ? index : 0;
}
