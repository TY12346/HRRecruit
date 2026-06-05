export const formatDateTime = (value) => {
  if (!value) return '—';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
};

export const formatDateInput = (value) => {
  if (!value) return '';
  return new Date(value).toISOString().slice(0, 16);
};

export const titleize = (value) => {
  if (!value) return '—';
  return String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
};

export const getApiErrorMessage = (error, fallback = 'Something went wrong.') => {
  const data = error?.response?.data;
  if (!data) return error?.message ?? fallback;
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const [firstKey] = Object.keys(data);
  const firstValue = data[firstKey];
  if (Array.isArray(firstValue)) return `${titleize(firstKey)}: ${firstValue.join(' ')}`;
  if (typeof firstValue === 'string') return `${titleize(firstKey)}: ${firstValue}`;
  return fallback;
};

export const candidateName = (interview) => interview?.application?.applicant?.full_name ?? 'Candidate';
export const jobTitle = (interview) => interview?.application?.job_title ?? 'Job';

export const latestInviteStatus = (interview) => titleize(interview?.latest_invitation?.status ?? 'not_sent');

export const getStoredRecordingId = (interviewId) => window.localStorage.getItem(`hrrecruit.interview.${interviewId}.recordingId`) ?? '';
export const setStoredRecordingId = (interviewId, recordingId) => window.localStorage.setItem(`hrrecruit.interview.${interviewId}.recordingId`, recordingId);
export const getStoredTranscriptId = (interviewId) => window.localStorage.getItem(`hrrecruit.interview.${interviewId}.transcriptId`) ?? '';
export const setStoredTranscriptId = (interviewId, transcriptId) => window.localStorage.setItem(`hrrecruit.interview.${interviewId}.transcriptId`, transcriptId);
export const getStoredSummaryId = (interviewId) => window.localStorage.getItem(`hrrecruit.interview.${interviewId}.summaryId`) ?? '';
export const setStoredSummaryId = (interviewId, summaryId) => window.localStorage.setItem(`hrrecruit.interview.${interviewId}.summaryId`, summaryId);
