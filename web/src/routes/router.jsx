import { Navigate, createBrowserRouter } from 'react-router-dom';
import PortalLayout from '../layouts/PortalLayout.jsx';
import LoginPage from '../pages/auth/LoginPage.jsx';
import RegisterApplicantPage from '../pages/auth/RegisterApplicantPage.jsx';
import RecruiterDashboardPage from '../pages/recruiter/RecruiterDashboardPage.jsx';
import InterviewerDashboardPage from '../pages/interviewer/InterviewerDashboardPage.jsx';
import HRHeadDashboardPage from '../pages/hr_head/HRHeadDashboardPage.jsx';
import OrganizationProfilePage from '../pages/hr_head/OrganizationProfilePage.jsx';
import TeamMembersPage from '../pages/hr_head/TeamMembersPage.jsx';
import CreateTeamMemberPage from '../pages/hr_head/CreateTeamMemberPage.jsx';
import BulkImportMembersPage from '../pages/hr_head/BulkImportMembersPage.jsx';
import PendingHiringDecisionsPage from '../pages/hr_head/PendingHiringDecisionsPage.jsx';
import BillingPage from '../pages/hr_head/BillingPage.jsx';
import HRAnalyticsPage from '../pages/hr_head/HRAnalyticsPage.jsx';
import NotificationsPage from '../pages/hr_head/NotificationsPage.jsx';
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
        children: [
          { path: 'hr-head', element: <HRHeadDashboardPage /> },
          { path: 'hr-head/organization', element: <OrganizationProfilePage /> },
          { path: 'hr-head/team', element: <TeamMembersPage /> },
          { path: 'hr-head/team/create', element: <CreateTeamMemberPage /> },
          { path: 'hr-head/team/bulk-import', element: <BulkImportMembersPage /> },
          { path: 'hr-head/hiring-decisions', element: <PendingHiringDecisionsPage /> },
          { path: 'hr-head/billing', element: <BillingPage /> },
          { path: 'hr-head/analytics', element: <HRAnalyticsPage /> },
          { path: 'hr-head/notifications', element: <NotificationsPage /> },
        ],
      },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
