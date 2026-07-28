import axios from 'axios';
import { useAuthStore } from '../store/authStore.js';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const accessToken = useAuthStore.getState().accessToken;

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

export const login = async ({ email, password }) => {
  const response = await apiClient.post('/auth/login/', { email, password });
  return response.data;
};

export const registerHiringManager = async ({ email, fullName, phoneNumber, password }) => {
  const response = await apiClient.post('/auth/register/', {
    email,
    full_name: fullName,
    phone_number: phoneNumber,
    password,
  });
  return response.data;
};

export const getProfile = async () => {
  const response = await apiClient.get('/auth/profile/');
  return response.data;
};

export const updateProfile = async (profile) => {
  const response = await apiClient.patch('/auth/profile/', profile);
  return response.data;
};

export const requestPasswordReset = async ({ email }) => {
  const response = await apiClient.post('/auth/password-reset/request/', { email, client_app: 'web' });
  return response.data;
};

export const confirmPasswordReset = async ({ email, resetToken, newPassword }) => {
  const response = await apiClient.post('/auth/password-reset/confirm/', {
    email,
    client_app: 'web',
    reset_token: resetToken,
    new_password: newPassword,
  });
  return response.data;
};


export const uploadResume = async ({ title, resumeFile, isDefault = false }) => {
  const formData = new FormData();
  formData.append('resume_file', resumeFile);
  if (title) {
    formData.append('title', title);
  }
  if (isDefault) {
    formData.append('is_default', 'true');
  }
  const response = await apiClient.post('/auth/resumes/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const updateResume = async (resumeId, payload) => {
  const response = await apiClient.patch(`/auth/resumes/${resumeId}/`, payload);
  return response.data;
};

export const deleteResume = async (resumeId) => {
  const response = await apiClient.delete(`/auth/resumes/${resumeId}/`);
  return response.data;
};

export const changePassword = async ({ currentPassword, newPassword }) => {
  const response = await apiClient.post('/auth/password/change/', {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return response.data;
};

export const logout = async (refreshToken) => {
  const response = await apiClient.post('/auth/logout/', { refresh: refreshToken });
  return response.data;
};

export const getOrganization = async () => {
  const response = await apiClient.get('/org/');
  return response.data;
};

export const createOrganization = async (organization) => {
  const response = await apiClient.post('/org/create/', organization);
  return response.data;
};

export const updateOrganization = async (organization) => {
  const response = await apiClient.patch('/org/', organization);
  return response.data;
};

export const deleteOrganization = async () => {
  const response = await apiClient.delete('/org/');
  return response.data;
};

export const getOrganizationMembers = async (search = '') => {
  const response = await apiClient.get('/org/members/', { params: search ? { search } : {} });
  return response.data;
};

export const createOrganizationMember = async (member) => {
  const response = await apiClient.post('/org/members/', member);
  return response.data;
};

export const bulkImportOrganizationMembers = async (members) => {
  const response = await apiClient.post('/org/members/bulk/', { members });
  return response.data;
};

export const deactivateOrganizationMember = async (memberId) => {
  const response = await apiClient.patch(`/org/members/${memberId}/deactivate/`);
  return response.data;
};

export const getPendingHiringDecisions = async () => {
  const response = await apiClient.get('/hiring-decisions/pending/');
  return response.data;
};

export const approveHiringDecision = async (decisionId, justification) => {
  const response = await apiClient.post(`/hiring-decisions/${decisionId}/approve/`, { justification });
  return response.data;
};

export const rejectHiringDecision = async (decisionId, justification) => {
  const response = await apiClient.post(`/hiring-decisions/${decisionId}/reject/`, { justification });
  return response.data;
};

export const getBillingPlans = async () => {
  const response = await apiClient.get('/billing/plans/');
  return response.data;
};

export const getCurrentSubscription = async () => {
  const response = await apiClient.get('/billing/subscription/');
  return response.data;
};

export const getHiringManagerOnboardingStatus = async () => {
  const response = await apiClient.get('/billing/onboarding-status/');
  return response.data;
};

export const getBillingInvoices = async () => {
  const response = await apiClient.get('/billing/invoices/');
  return response.data;
};

export const subscribeToPlan = async ({ planId, isAutoRenew = false }) => {
  const response = await apiClient.post('/billing/subscribe/', {
    plan_id: planId,
    is_auto_renew: isAutoRenew,
  });
  return response.data;
};

export const upgradeSubscription = async ({ planId, isAutoRenew = false }) => {
  const response = await apiClient.post('/billing/upgrade/', {
    plan_id: planId,
    is_auto_renew: isAutoRenew,
  });
  return response.data;
};

export const completeDemoPayment = async ({ subscriptionId, transactionReference }) => {
  const response = await apiClient.post('/billing/demo-payment-success/', {
    subscription_id: subscriptionId,
    transaction_reference: transactionReference,
  });
  return response.data;
};

export const cancelSubscription = async ({ reason = '' } = {}) => {
  const response = await apiClient.post('/billing/subscription/cancel/', { reason });
  return response.data;
};

export const reactivateSubscription = async () => {
  const response = await apiClient.post('/billing/subscription/reactivate/');
  return response.data;
};

export const getHiringManagerAnalytics = async () => {
  const response = await apiClient.get('/analytics/hiring-manager/dashboard/');
  return response.data;
};

export const getOrganizationAnalyticsOverview = async () => {
  const response = await apiClient.get('/analytics/organization/overview/');
  return response.data;
};

export const getNotifications = async () => {
  const response = await apiClient.get('/notifications/');
  return response.data;
};

export const getNotification = async (notificationId) => {
  const response = await apiClient.get(`/notifications/${notificationId}/`);
  return response.data;
};

export const markNotificationRead = async (notificationId) => {
  const response = await apiClient.patch(`/notifications/${notificationId}/read/`);
  return response.data;
};

export const markAllNotificationsRead = async () => {
  const response = await apiClient.patch('/notifications/read-all/');
  return response.data;
};

export const getUnreadNotificationCount = async () => {
  const response = await apiClient.get('/notifications/unread-count/');
  return response.data;
};

export default apiClient;


export const downloadAnalyticsReportPdf = async (reportType) => {
  const reportPaths = {
    recruiter: '/reports/recruiter-summary.pdf',
    interviewer: '/reports/interviewer-summary.pdf',
    hr_head: '/reports/hiring-manager-summary.pdf',
  };
  const reportPath = reportPaths[reportType];

  if (!reportPath) {
    throw new Error('Unsupported analytics report type.');
  }

  const response = await apiClient.get(reportPath, { responseType: 'blob' });
  return response.data;
};

export const getRecruiterAnalytics = async () => {
  const response = await apiClient.get('/analytics/recruiter/dashboard/');
  return response.data;
};

export const getJobFunnelAnalytics = async (jobId) => {
  const response = await apiClient.get(`/analytics/jobs/${jobId}/funnel/`);
  return response.data;
};

export const getJobs = async () => {
  const response = await apiClient.get('/jobs/');
  return response.data;
};


export const getJobRequisitions = async () => {
  const response = await apiClient.get('/jobs/requisitions/');
  return response.data;
};

export const createJobRequisition = async (requisition) => {
  const response = await apiClient.post('/jobs/requisitions/', requisition);
  return response.data;
};

export const approveJobRequisition = async (requisitionId) => {
  const response = await apiClient.post(`/jobs/requisitions/${requisitionId}/approve/`);
  return response.data;
};

export const rejectJobRequisition = async (requisitionId, reason) => {
  const response = await apiClient.post(`/jobs/requisitions/${requisitionId}/reject/`, { reason });
  return response.data;
};

export const getJob = async (jobId) => {
  const response = await apiClient.get(`/jobs/${jobId}/`);
  return response.data;
};

export const createJob = async (job) => {
  const response = await apiClient.post('/jobs/', job);
  return response.data;
};

export const updateJob = async (jobId, job) => {
  const response = await apiClient.patch(`/jobs/${jobId}/`, job);
  return response.data;
};

export const closeJobApplicationIntake = async (jobId) => (await apiClient.post(`/jobs/${jobId}/close-intake/`)).data;
export const getJobApplicantComparison = async (jobId) => (await apiClient.get(`/jobs/${jobId}/applicant-comparison/`)).data;
export const submitJobHiringDecision = async (payload) => (await apiClient.post('/job-hiring-decisions/', payload)).data;
export const getJobHiringDecisions = async (params = {}) => (await apiClient.get('/job-hiring-decisions/', { params })).data;
export const approveJobHiringDecision = async (id, hr_remarks) => (await apiClient.post(`/job-hiring-decisions/${id}/approve/`, { hr_remarks })).data;
export const rejectJobHiringDecision = async (id, hr_remarks) => (await apiClient.post(`/job-hiring-decisions/${id}/reject/`, { hr_remarks })).data;

export const deleteJob = async (jobId) => {
  const response = await apiClient.delete(`/jobs/${jobId}/`);
  return response.data;
};

export const duplicateJob = async (jobId) => {
  const response = await apiClient.post(`/jobs/${jobId}/duplicate/`);
  return response.data;
};

export const configureJobRequirements = async (jobId, payload) => {
  const response = await apiClient.post(`/jobs/${jobId}/requirements/`, payload);
  return response.data;
};

export const createInterviewEvaluationScorecard = async (jobId, payload) => {
  const response = await apiClient.post(`/jobs/${jobId}/scorecard/`, payload);
  return response.data;
};

export const createJobEvaluationForm = createInterviewEvaluationScorecard;

export const getApplications = async (params = {}) => {
  const response = await apiClient.get('/applications/', { params });
  return response.data;
};

export const getApplicantSearch = async (params = {}) => {
  const response = await apiClient.get('/applications/search/', { params });
  return response.data;
};

export const getEmployerInvites = async () => (await apiClient.get('/applications/employer-invites/')).data;
export const sendEmployerInvite = async (payload) => (await apiClient.post('/applications/employer-invites/', payload)).data;

export const getApplication = async (applicationId) => {
  const response = await apiClient.get(`/applications/${applicationId}/`);
  return response.data;
};


export const openApplicationResume = async (applicationId) => {
  const response = await apiClient.get(`/applications/${applicationId}/resume/`, { responseType: 'blob' });
  const resumeBlob = new Blob([response.data], { type: response.headers['content-type'] });
  const resumeUrl = window.URL.createObjectURL(resumeBlob);
  window.open(resumeUrl, '_blank', 'noopener,noreferrer');
  window.setTimeout(() => window.URL.revokeObjectURL(resumeUrl), 60000);
};

export const screenApplication = async (applicationId) => {
  const response = await apiClient.post(`/applications/${applicationId}/screen/`);
  return response.data;
};

export const getApplicantProfile = async (applicationId) => {
  const response = await apiClient.get(`/applications/${applicationId}/applicant-profile/`);
  return response.data;
};

export const shortlistApplication = async (applicationId, payload) => {
  const response = await apiClient.post(`/applications/${applicationId}/shortlist/`, payload);
  return response.data;
};

export const assignInterviewer = async (applicationId, payload) => {
  const response = await apiClient.post(`/applications/${applicationId}/assign-interviewer/`, payload);
  return response.data;
};

export const createInterviewSchedulingRequest = async (applicationId, payload) => {
  const response = await apiClient.post(`/applications/${applicationId}/scheduling-request/`, payload);
  return response.data;
};

export const getInterviewSchedulingRequests = async () => {
  const response = await apiClient.get('/interviews/scheduling-requests/');
  return response.data;
};

export const rejectApplication = async (applicationId, payload) => {
  const response = await apiClient.post(`/applications/${applicationId}/reject/`, payload);
  return response.data;
};

export const updateApplicationRemark = async (applicationId, remark) => {
  const response = await apiClient.patch(`/applications/${applicationId}/remark/`, { remark });
  return response.data;
};

export const getApplicationStatusHistory = async (applicationId) => {
  const response = await apiClient.get(`/applications/${applicationId}/status-history/`);
  return response.data;
};

export const getRankedApplicants = async (jobId, params = {}) => {
  const response = await apiClient.get(`/jobs/${jobId}/ranked-applicants/`, { params });
  return response.data;
};

export const getInterviews = async (params = {}) => {
  const response = await apiClient.get('/interviews/', { params });
  return response.data;
};

export const getInterviewEvaluationDetail = async (interviewId) => {
  const response = await apiClient.get(`/interviews/${interviewId}/evaluation-detail/`);
  return response.data;
};

export const submitHiringDecision = async (applicationId, payload) => {
  const response = await apiClient.post(`/applications/${applicationId}/hiring-decision/`, payload);
  return response.data;
};

export const getHiringDecision = async (decisionId) => {
  const response = await apiClient.get(`/hiring-decisions/${decisionId}/`);
  return response.data;
};

export const getJobOffers = async (params = {}) => {
  const response = await apiClient.get('/job-offers/', { params });
  return response.data;
};

export const sendJobOffer = async (applicationId, payload) => {
  const hasFile = payload.offer_letter_file instanceof File;
  const cleanedPayload = Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== undefined && value !== null && value !== '')
  );
  const body = hasFile ? new FormData() : cleanedPayload;
  if (hasFile) {
    Object.entries(cleanedPayload).forEach(([key, value]) => {
      body.append(key, value);
    });
  }
  const response = await apiClient.post(`/applications/${applicationId}/job-offer/`, body, {
    headers: hasFile ? { 'Content-Type': 'multipart/form-data' } : undefined,
  });
  return response.data;
};

export const withdrawJobOffer = async (offerId, payload = {}) => {
  const response = await apiClient.post(`/job-offers/${offerId}/withdraw/`, payload);
  return response.data;
};

export const approveJobOffer = async (offerId, remarks = '') =>
  (await apiClient.post(`/job-offers/${offerId}/approve/`, { remarks })).data;
export const disapproveJobOffer = async (offerId, remarks) =>
  (await apiClient.post(`/job-offers/${offerId}/disapprove/`, { remarks })).data;
export const sendApprovedJobOffer = async (offerId) =>
  (await apiClient.post(`/job-offers/${offerId}/send/`)).data;
export const resubmitJobOffer = async (offerId, payload) =>
  (await apiClient.patch(`/job-offers/${offerId}/resubmit/`, payload)).data;

export const getGoogleCalendarStatus = async () => {
  const response = await apiClient.get('/interviews/calendar/google/status/');
  return response.data;
};

export const getGoogleCalendarConnectUrl = async (nextUrl = '') => {
  const response = await apiClient.get('/interviews/calendar/google/connect/', {
    params: nextUrl ? { next: nextUrl } : {},
  });
  return response.data;
};

export const completeGoogleCalendarOAuth = async ({ code, state }) => {
  const response = await apiClient.post('/interviews/calendar/google/callback/', { code, state });
  return response.data;
};

export const disconnectGoogleCalendar = async () => {
  const response = await apiClient.delete('/interviews/calendar/google/disconnect/');
  return response.data;
};

export const getAssignedInterviews = async () => {
  const response = await apiClient.get('/interviews/assigned/');
  return response.data;
};

export const getInterviewerAvailabilityPatterns = async () => {
  const response = await apiClient.get('/interviews/availability/patterns/');
  return response.data;
};

export const createInterviewerAvailabilityPattern = async (payload) => {
  const response = await apiClient.post('/interviews/availability/patterns/', payload);
  return response.data;
};

export const updateInterviewerAvailabilityPattern = async (patternId, payload) => {
  const response = await apiClient.patch(`/interviews/availability/patterns/${patternId}/`, payload);
  return response.data;
};

export const deactivateInterviewerAvailabilityPattern = async (patternId) => {
  const response = await apiClient.delete(`/interviews/availability/patterns/${patternId}/`);
  return response.data;
};

export const getInterviewerUnavailableDates = async () => {
  const response = await apiClient.get('/interviews/availability/unavailable-dates/');
  return response.data;
};

export const createInterviewerUnavailableDate = async (payload) => {
  const response = await apiClient.post('/interviews/availability/unavailable-dates/', payload);
  return response.data;
};

export const deleteInterviewerUnavailableDate = async (unavailableDateId) => {
  await apiClient.delete(`/interviews/availability/unavailable-dates/${unavailableDateId}/`);
};

export const getInterviewerAvailabilitySlots = async () => {
  const response = await apiClient.get('/interviews/availability/');
  return response.data;
};

export const createInterviewerAvailabilitySlot = async (payload) => {
  const response = await apiClient.post('/interviews/availability/', payload);
  return response.data;
};

export const cancelInterviewerAvailabilitySlot = async (slotId) => {
  const response = await apiClient.delete(`/interviews/availability/${slotId}/`);
  return response.data;
};

export const getInterview = async (interviewId) => {
  const response = await apiClient.get(`/interviews/${interviewId}/`);
  return response.data;
};

export const uploadInterviewRecording = async (interviewId, audioFile) => {
  const formData = new FormData();
  formData.append('audio_file', audioFile);
  const response = await apiClient.post(`/interviews/${interviewId}/recordings/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const transcribeRecording = async (recordingId) => {
  const response = await apiClient.post(`/recordings/${recordingId}/transcribe/`);
  return response.data;
};

export const generateTranscriptSummary = async (transcriptId) => {
  const response = await apiClient.post(`/transcripts/${transcriptId}/generate-summary/`);
  return response.data;
};

export const updateInterviewSummary = async (summaryId, payload) => {
  const response = await apiClient.patch(`/interview-summaries/${summaryId}/`, payload);
  return response.data;
};

export const submitInterviewEvaluation = async (interviewId, payload) => {
  const response = await apiClient.post(`/interviews/${interviewId}/evaluations/`, payload);
  return response.data;
};

export const getInterviewerAnalytics = async () => {
  const response = await apiClient.get('/analytics/interviewer/dashboard/');
  return response.data;
};
