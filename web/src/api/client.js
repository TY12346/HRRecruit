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

export default apiClient;
