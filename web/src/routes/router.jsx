import { Navigate, createBrowserRouter } from 'react-router-dom';
import PortalLayout from '../layouts/PortalLayout.jsx';
import LoginPage from '../pages/auth/LoginPage.jsx';
import RecruiterDashboardPage from '../pages/recruiter/RecruiterDashboardPage.jsx';
import InterviewerDashboardPage from '../pages/interviewer/InterviewerDashboardPage.jsx';
import HrHeadDashboardPage from '../pages/hr_head/HrHeadDashboardPage.jsx';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <PortalLayout />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'recruiter', element: <RecruiterDashboardPage /> },
      { path: 'interviewer', element: <InterviewerDashboardPage /> },
      { path: 'hr-head', element: <HrHeadDashboardPage /> },
    ],
  },
]);
