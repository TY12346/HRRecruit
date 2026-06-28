const TEMPLATE_GROUPS = {
  interview_self_scheduling: [
    {
      id: 'self_schedule_standard',
      label: 'Self-scheduling invitation',
      tone: 'Professional',
      body: 'Hi {{candidateName}},\n\nThank you for your interest in {{jobTitle}}. We would like to invite you to the next interview stage. Please choose a suitable interview slot from the available times in HRRecruit.\n\nBest regards,\n{{recruiterName}}',
    },
    {
      id: 'self_schedule_warm',
      label: 'Warm interview invitation',
      tone: 'Warm',
      body: 'Hi {{candidateName}},\n\nYour application for {{jobTitle}} stood out to our team. We would be happy to continue with an interview. Please select a time that works best for you in HRRecruit.\n\nBest regards,\n{{recruiterName}}',
    },
  ],
  manual_interview_assignment: [
    {
      id: 'manual_assignment_internal',
      label: 'Interviewer briefing note',
      tone: 'Internal',
      body: 'Please review {{candidateName}} for {{jobTitle}}. Focus on role fit, communication, and the key requirements configured for this job. Add evaluation notes after the interview.',
    },
  ],
  rejection: [
    {
      id: 'rejection_general',
      label: 'General rejection',
      tone: 'Polite',
      body: 'Hi {{candidateName}},\n\nThank you for applying for {{jobTitle}}. After careful review, we will not be moving forward with your application at this time. We appreciate your interest in {{companyName}} and wish you all the best in your job search.\n\nBest regards,\n{{recruiterName}}',
    },
    {
      id: 'rejection_after_interview',
      label: 'After interview rejection',
      tone: 'Respectful',
      body: 'Hi {{candidateName}},\n\nThank you for taking the time to interview for {{jobTitle}}. After reviewing the interview feedback, we have decided to proceed with other candidates whose experience more closely matches the current role requirements. We appreciate your time and interest in {{companyName}}.\n\nBest regards,\n{{recruiterName}}',
    },
  ],
  offer: [
    {
      id: 'offer_standard',
      label: 'Standard offer',
      tone: 'Formal',
      body: 'Hi {{candidateName}},\n\nCongratulations. HR has approved your hiring decision and we are pleased to extend an offer for {{jobTitle}} at {{companyName}}. Please review the offer details and respond by {{deadline}} in HRRecruit.\n\nBest regards,\n{{recruiterName}}',
    },
    {
      id: 'offer_warm',
      label: 'Warm offer',
      tone: 'Warm',
      body: 'Hi {{candidateName}},\n\nCongratulations from all of us at {{companyName}}. We enjoyed getting to know you and are excited to offer you the {{jobTitle}} position. Please review the offer and respond by {{deadline}} in HRRecruit.\n\nBest regards,\n{{recruiterName}}',
    },
  ],
};

const DEFAULT_CONTEXT = {
  candidateName: 'Candidate',
  jobTitle: 'this role',
  companyName: 'our organization',
  recruiterName: 'Recruitment Team',
  deadline: 'the response deadline',
};

export function getCommunicationTemplates(type) {
  return TEMPLATE_GROUPS[type] ?? [];
}

export function getCommunicationTemplate(type, templateId) {
  return getCommunicationTemplates(type).find((template) => template.id === templateId) ?? getCommunicationTemplates(type)[0] ?? null;
}

export function renderCommunicationTemplate(templateOrBody, context = {}) {
  const body = typeof templateOrBody === 'string' ? templateOrBody : templateOrBody?.body ?? '';
  const mergedContext = { ...DEFAULT_CONTEXT, ...context };
  return Object.entries(mergedContext).reduce(
    (message, [key, value]) => message.replaceAll(`{{${key}}}`, value || DEFAULT_CONTEXT[key] || ''),
    body,
  );
}

export function buildApplicationTemplateContext(application = {}, overrides = {}) {
  const applicant = application.applicant ?? application.applicant_profile ?? {};
  return {
    candidateName: applicant.full_name ?? application.candidate_name ?? DEFAULT_CONTEXT.candidateName,
    jobTitle: application.job_title ?? application.job?.title ?? DEFAULT_CONTEXT.jobTitle,
    companyName: application.organization_name ?? application.job?.organization_name ?? DEFAULT_CONTEXT.companyName,
    recruiterName: overrides.recruiterName ?? DEFAULT_CONTEXT.recruiterName,
    ...overrides,
  };
}

export function renderApplicationTemplate(type, templateId, application = {}, overrides = {}) {
  const template = getCommunicationTemplate(type, templateId);
  return renderCommunicationTemplate(template, buildApplicationTemplateContext(application, overrides));
}
