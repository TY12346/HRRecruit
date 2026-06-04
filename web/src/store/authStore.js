import { create } from 'zustand';

const STORAGE_KEY = 'hrrecruit.auth';

const readStoredSession = () => {
  if (typeof window === 'undefined') {
    return { accessToken: null, refreshToken: null, user: null };
  }

  try {
    const storedSession = window.localStorage.getItem(STORAGE_KEY);
    return storedSession
      ? JSON.parse(storedSession)
      : { accessToken: null, refreshToken: null, user: null };
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return { accessToken: null, refreshToken: null, user: null };
  }
};

const writeStoredSession = (session) => {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
};

const clearStoredSession = () => {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.removeItem(STORAGE_KEY);
};

const initialSession = readStoredSession();

export const useAuthStore = create((set, get) => ({
  accessToken: initialSession.accessToken,
  refreshToken: initialSession.refreshToken,
  user: initialSession.user,
  isAuthenticated: Boolean(initialSession.accessToken),
  setSession: ({ accessToken, refreshToken, user }) => {
    const session = { accessToken, refreshToken, user };
    writeStoredSession(session);
    set({ ...session, isAuthenticated: Boolean(accessToken) });
  },
  updateUser: (user) => {
    const session = {
      accessToken: get().accessToken,
      refreshToken: get().refreshToken,
      user,
    };
    writeStoredSession(session);
    set({ user });
  },
  clearSession: () => {
    clearStoredSession();
    set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
  },
}));

export const authStorageKey = STORAGE_KEY;
