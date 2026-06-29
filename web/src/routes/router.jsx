import { Navigate, createBrowserRouter } from 'react-router-dom';
import PortalLayout from '../layouts/PortalLayout.jsx';
import LoginPage from '../pages/auth/LoginPage.jsx';
import ForgotPasswordPage from '../pages/auth/ForgotPasswordPage.jsx';
import ResetPasswordPage from '../pages/auth/ResetPasswordPage.jsx';
import RegisterHRHeadPage from '../pages/auth/RegisterHRHeadPage.jsx';
import RecruiterDashboardPage from '../pages/recruiter/RecruiterDashboardPage.jsx';
import ApplicationsPage from '../pages/recruiter/ApplicationsPage.jsx';
import CandidateProfilePage from '../pages/recruiter/CandidateProfilePage.jsx';
import CandidateRankingPage from '../pages/recruiter/CandidateRankingPage.jsx';
import EvaluationFormBuilderPage from '../pages/recruiter/EvaluationFormBuilderPage.jsx';
import HiringDecisionPage from '../pages/recruiter/HiringDecisionPage.jsx';
import InterviewAssignmentPage from '../pages/recruiter/InterviewAssignmentPage.jsx';
import GoogleCalendarCallbackPage from '../pages/recruiter/GoogleCalendarCallbackPage.jsx';
import InterviewEvaluationDetailPage from '../pages/recruiter/InterviewEvaluationDetailPage.jsx';
import JobCreateEditPage from '../pages/recruiter/JobCreateEditPage.jsx';
import JobDetailPage from '../pages/recruiter/JobDetailPage.jsx';
import JobListPage from '../pages/recruiter/JobListPage.jsx';
import JobOfferPage from '../pages/recruiter/JobOfferPage.jsx';
import JobRequirementsPage from '../pages/recruiter/JobRequirementsPage.jsx';
import RecruiterAnalyticsPage from '../pages/recruiter/RecruiterAnalyticsPage.jsx';
import RecruiterNotificationsPage from '../pages/recruiter/NotificationsPage.jsx';
import InterviewerDashboardPage from '../pages/interviewer/InterviewerDashboardPage.jsx';
import AvailabilityPage from '../pages/interviewer/AvailabilityPage.jsx';
import AssignedCandidatesPage from '../pages/interviewer/AssignedCandidatesPage.jsx';
import CandidateDetailPage from '../pages/interviewer/CandidateDetailPage.jsx';
import InterviewerInterviewDetailPage from '../pages/interviewer/InterviewDetailPage.jsx';
import InterviewListPage from '../pages/interviewer/InterviewListPage.jsx';
import InterviewerAnalyticsPage from '../pages/interviewer/InterviewerAnalyticsPage.jsx';
import InterviewerNotificationsPage from '../pages/interviewer/NotificationsPage.jsx';
import SubmitEvaluationPage from '../pages/interviewer/SubmitEvaluationPage.jsx';
import TranscriptSummaryPage from '../pages/interviewer/TranscriptSummaryPage.jsx';
import UploadRecordingPage from '../pages/interviewer/UploadRecordingPage.jsx';
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

const githubPagesBasename = window.location.hostname.endsWith('github.io')
  ? `/${window.location.pathname.split('/').filter(Boolean)[0] || ''}`
  : '';
const configuredBasename = import.meta.env.VITE_ROUTER_BASENAME || githubPagesBasename || import.meta.env.BASE_URL;
const routerBasename = configuredBasename && !['/', './'].includes(configuredBasename)
  ? configuredBasename.replace(/\/$/, '')
  : undefined;

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
          { path: 'forgot-password', element: <ForgotPasswordPage /> },
          { path: 'reset-password', element: <ResetPasswordPage /> },
          { path: 'register', element: <RegisterHRHeadPage /> },
          { path: 'register-applicant', element: <Navigate to="/register" replace /> },
        ],
      },
      {
        element: <ProtectedRoute />,
        children: [{ path: 'profile', element: <ProfilePage /> }],
      },
      {
        element: <RoleRoute allowedRoles={['recruiter']} />,
        children: [
          { path: 'recruiter', element: <RecruiterDashboardPage /> },
          { path: 'recruiter/jobs', element: <JobListPage /> },
          { path: 'recruiter/jobs/create', element: <JobCreateEditPage /> },
          { path: 'recruiter/jobs/:jobId', element: <JobDetailPage /> },
          { path: 'recruiter/jobs/:jobId/edit', element: <JobCreateEditPage /> },
          { path: 'recruiter/jobs/:jobId/requirements', element: <JobRequirementsPage /> },
          { path: 'recruiter/jobs/:jobId/evaluation-form', element: <EvaluationFormBuilderPage /> },
          { path: 'recruiter/jobs/:jobId/ranking', element: <CandidateRankingPage /> },
          { path: 'recruiter/applications', element: <ApplicationsPage /> },
          { path: 'recruiter/applications/:applicationId', element: <CandidateProfilePage /> },
          { path: 'recruiter/applications/:applicationId/assign-interview', element: <InterviewAssignmentPage /> },
          { path: 'recruiter/applications/:applicationId/hiring-decision', element: <HiringDecisionPage /> },
          { path: 'recruiter/interviews', element: <InterviewEvaluationDetailPage /> },
          { path: 'recruiter/calendar/google/callback', element: <GoogleCalendarCallbackPage /> },
          { path: 'recruiter/hiring-decisions', element: <HiringDecisionPage /> },
          { path: 'recruiter/job-offers', element: <JobOfferPage /> },
          { path: 'recruiter/analytics', element: <RecruiterAnalyticsPage /> },
          { path: 'recruiter/notifications', element: <RecruiterNotificationsPage /> },
        ],
      },
      {
        element: <RoleRoute allowedRoles={['interviewer']} />,
        children: [
          { path: 'interviewer', element: <InterviewerDashboardPage /> },
          { path: 'interviewer/candidates', element: <AssignedCandidatesPage /> },
          { path: 'interviewer/candidates/:applicationId', element: <CandidateDetailPage /> },
          { path: 'interviewer/interviews', element: <InterviewListPage /> },
          { path: 'interviewer/interviews/:interviewId', element: <InterviewerInterviewDetailPage /> },
          { path: 'interviewer/interviews/:interviewId/recording', element: <UploadRecordingPage /> },
          { path: 'interviewer/interviews/:interviewId/transcript-summary', element: <TranscriptSummaryPage /> },
          { path: 'interviewer/interviews/:interviewId/evaluation', element: <SubmitEvaluationPage /> },
          { path: 'interviewer/availability', element: <AvailabilityPage /> },
          { path: 'interviewer/analytics', element: <InterviewerAnalyticsPage /> },
          { path: 'interviewer/notifications', element: <InterviewerNotificationsPage /> },
        ],
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
], { basename: routerBasename });
