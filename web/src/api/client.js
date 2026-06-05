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

export const registerApplicant = async ({ email, fullName, phoneNumber, password }) => {
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

export const getOrganizationMembers = async (search = '') => {
  const response = await apiClient.get('/org/members/', { params: search ? { search } : {} });
  return response.data;
};

export const createOrganizationMember = async (member) => {
  const response = await apiClient.post('/org/members/', member);
  return response.data;
};

export const bulkImportOrganizationMembers = async (csvFile) => {
  const formData = new FormData();
  formData.append('csv_file', csvFile);
  const response = await apiClient.post('/org/members/bulk/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
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

export const getHRHeadAnalytics = async () => {
  const response = await apiClient.get('/analytics/hr-head/dashboard/');
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
