import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Alert, Box, CircularProgress } from '@mui/material';
import { useEffect, useState } from 'react';
import { getHiringManagerOnboardingStatus } from '../api/client.js';
import { useAuthStore } from '../store/authStore.js';

export const roleDashboardPaths = {
  applicant: '/profile',
  recruiter: '/recruiter',
  interviewer: '/interviewer',
  hr_head: '/hiring-manager',
};

export function getDashboardPathForRole(role) {
  return roleDashboardPaths[role] ?? '/profile';
}

export function DashboardRedirect() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Navigate to={getDashboardPathForRole(user?.role)} replace />;
}

export function GuestOnlyRoute() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to={getDashboardPathForRole(user?.role)} replace />;
  }

  return <Outlet />;
}

export function ProtectedRoute() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (user?.role === 'hr_head') {
    return <HiringManagerOnboardingRoute />;
  }

  return <Outlet />;
}

export function RoleRoute({ allowedRoles }) {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!allowedRoles.includes(user?.role)) {
    return <Navigate to={getDashboardPathForRole(user?.role)} replace />;
  }

  return <Outlet />;
}

export function HiringManagerOnboardingRoute() {
  const location = useLocation();
  const [status, setStatus] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    getHiringManagerOnboardingStatus()
      .then((data) => {
        if (isMounted) {
          setStatus({ ...data, path: location.pathname });
        }
      })
      .catch(() => {
        if (isMounted) {
          setError('Unable to verify your workspace setup. Please refresh and try again.');
        }
      });

    return () => {
      isMounted = false;
    };
  }, [location.pathname]);

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!status || status.path !== location.pathname) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
        <CircularProgress aria-label="Checking workspace setup" />
      </Box>
    );
  }

  if (!status.organization_created && location.pathname !== '/hiring-manager/onboarding/organization') {
    return <Navigate to="/hiring-manager/onboarding/organization" replace />;
  }

  if (status.organization_created && !status.subscription_selected && location.pathname !== '/hiring-manager/onboarding/subscription') {
    return <Navigate to="/hiring-manager/onboarding/subscription" replace />;
  }

  return <Outlet />;
}
