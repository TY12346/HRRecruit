import { Navigate, createBrowserRouter } from 'react-router-dom';
import PortalLayout from '../layouts/PortalLayout.jsx';
import LoginPage from '../pages/auth/LoginPage.jsx';
import RegisterApplicantPage from '../pages/auth/RegisterApplicantPage.jsx';
import RecruiterDashboardPage from '../pages/recruiter/RecruiterDashboardPage.jsx';
import InterviewerDashboardPage from '../pages/interviewer/InterviewerDashboardPage.jsx';
import HrHeadDashboardPage from '../pages/hr_head/HrHeadDashboardPage.jsx';
import ProfilePage from '../pages/profile/ProfilePage.jsx';
import { DashboardRedirect, GuestOnlyRoute, ProtectedRoute, RoleRoute } from './guards.jsx';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <PortalLayout />,
    children: [
      { index: true, element: <DashboardRedirect /> },
      {
        element: <GuestOnlyRoute />,
        children: [
          { path: 'login', element: <LoginPage /> },
          { path: 'register-applicant', element: <RegisterApplicantPage /> },
        ],
      },
      {
        element: <ProtectedRoute />,
        children: [{ path: 'profile', element: <ProfilePage /> }],
      },
      {
        element: <RoleRoute allowedRoles={['recruiter']} />,
        children: [{ path: 'recruiter', element: <RecruiterDashboardPage /> }],
      },
      {
        element: <RoleRoute allowedRoles={['interviewer']} />,
        children: [{ path: 'interviewer', element: <InterviewerDashboardPage /> }],
      },
      {
        element: <RoleRoute allowedRoles={['hr_head']} />,
        children: [{ path: 'hr-head', element: <HrHeadDashboardPage /> }],
      },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
