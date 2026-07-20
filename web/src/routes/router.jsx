import { Navigate, createBrowserRouter } from 'react-router-dom';
import PortalLayout from '../layouts/PortalLayout.jsx';
import LoginPage from '../pages/auth/LoginPage.jsx';
import ForgotPasswordPage from '../pages/auth/ForgotPasswordPage.jsx';
import ResetPasswordPage from '../pages/auth/ResetPasswordPage.jsx';
import RegisterHiringManagerPage from '../pages/auth/RegisterHiringManagerPage.jsx';
import RecruiterDashboardPage from '../pages/recruiter/RecruiterDashboardPage.jsx';
import ApplicationsPage from '../pages/recruiter/ApplicationsPage.jsx';
import RoleBasedApplicantSearchPage from '../pages/applications/RoleBasedApplicantSearchPage.jsx';
import ApplicantProfilePage from '../pages/recruiter/ApplicantProfilePage.jsx';
import ApplicantRankingPage from '../pages/recruiter/ApplicantRankingPage.jsx';
import EvaluationScorecardBuilderPage from '../pages/recruiter/EvaluationFormBuilderPage.jsx';
import HiringDecisionPage from '../pages/recruiter/HiringDecisionPage.jsx';
import HiringDecisionsPage from '../pages/recruiter/HiringDecisionsPage.jsx';
import InterviewAssignmentPage from '../pages/recruiter/InterviewAssignmentPage.jsx';
import GoogleCalendarCallbackPage from '../pages/recruiter/GoogleCalendarCallbackPage.jsx';
import InterviewEvaluationDetailPage from '../pages/recruiter/InterviewEvaluationDetailPage.jsx';
import JobCreateEditPage from '../pages/recruiter/JobCreateEditPage.jsx';
import JobDetailPage from '../pages/recruiter/JobDetailPage.jsx';
import JobListPage from '../pages/recruiter/JobListPage.jsx';
import RecruiterJobRequisitionsPage from '../pages/recruiter/JobRequisitionsPage.jsx';
import JobOfferPage from '../pages/recruiter/JobOfferPage.jsx';
import JobRequirementsPage from '../pages/recruiter/JobRequirementsPage.jsx';
import RecruiterAnalyticsPage from '../pages/recruiter/RecruiterAnalyticsPage.jsx';
import RecruiterNotificationsPage from '../pages/recruiter/NotificationsPage.jsx';
import InterviewerDashboardPage from '../pages/interviewer/InterviewerDashboardPage.jsx';
import AvailabilityPage from '../pages/interviewer/AvailabilityPage.jsx';
import AssignedApplicantsPage from '../pages/interviewer/AssignedApplicantsPage.jsx';
import ApplicantDetailPage from '../pages/interviewer/ApplicantDetailPage.jsx';
import InterviewerInterviewDetailPage from '../pages/interviewer/InterviewDetailPage.jsx';
import InterviewListPage from '../pages/interviewer/InterviewListPage.jsx';
import InterviewerAnalyticsPage from '../pages/interviewer/InterviewerAnalyticsPage.jsx';
import InterviewerNotificationsPage from '../pages/interviewer/NotificationsPage.jsx';
import SubmitEvaluationPage from '../pages/interviewer/SubmitEvaluationPage.jsx';
import TranscriptSummaryPage from '../pages/interviewer/TranscriptSummaryPage.jsx';
import HiringManagerDashboardPage from '../pages/hiring_manager/HiringManagerDashboardPage.jsx';
import OrganizationProfilePage from '../pages/hiring_manager/OrganizationProfilePage.jsx';
import OrganizationOnboardingPage from '../pages/hiring_manager/OrganizationOnboardingPage.jsx';
import SubscriptionOnboardingPage from '../pages/hiring_manager/SubscriptionOnboardingPage.jsx';
import TeamMembersPage from '../pages/hiring_manager/TeamMembersPage.jsx';
import CreateTeamMemberPage from '../pages/hiring_manager/CreateTeamMemberPage.jsx';
import BulkImportMembersPage from '../pages/hiring_manager/BulkImportMembersPage.jsx';
import PendingHiringDecisionsPage from '../pages/hiring_manager/PendingHiringDecisionsPage.jsx';
import HiringManagerJobRequisitionsPage from '../pages/hiring_manager/HiringManagerJobRequisitionsPage.jsx';
import BillingPage from '../pages/hiring_manager/BillingPage.jsx';
import HiringManagerAnalyticsPage from '../pages/hiring_manager/HiringManagerAnalyticsPage.jsx';
import NotificationsPage from '../pages/hiring_manager/NotificationsPage.jsx';
import ProfilePage from '../pages/profile/ProfilePage.jsx';
import { DashboardRedirect, GuestOnlyRoute, HiringManagerOnboardingRoute, ProtectedRoute, RoleRoute } from './guards.jsx';

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
          { path: 'register', element: <RegisterHiringManagerPage /> },
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
          { path: 'recruiter/job-requisitions', element: <RecruiterJobRequisitionsPage /> },
          { path: 'recruiter/jobs/create', element: <JobCreateEditPage /> },
          { path: 'recruiter/jobs/:jobId', element: <JobDetailPage /> },
          { path: 'recruiter/jobs/:jobId/edit', element: <JobCreateEditPage /> },
          { path: 'recruiter/jobs/:jobId/requirements', element: <JobRequirementsPage /> },
          { path: 'recruiter/jobs/:jobId/scorecard', element: <EvaluationScorecardBuilderPage /> },
          { path: 'recruiter/jobs/:jobId/evaluation-form', element: <EvaluationScorecardBuilderPage /> },
          { path: 'recruiter/jobs/:jobId/ranking', element: <ApplicantRankingPage /> },
          { path: 'recruiter/jobs/:jobId/hiring-decision', element: <HiringDecisionPage /> },
          { path: 'recruiter/hiring-decisions', element: <HiringDecisionsPage /> },
          { path: 'recruiter/applications', element: <ApplicationsPage /> },
          { path: 'recruiter/applicant-search', element: <RoleBasedApplicantSearchPage role="recruiter" /> },
          { path: 'recruiter/applications/:applicationId', element: <ApplicantProfilePage /> },
          { path: 'recruiter/applications/:applicationId/assign-interview', element: <InterviewAssignmentPage /> },
          { path: 'recruiter/applications/:applicationId/hiring-decision', element: <Navigate to="/recruiter/jobs" replace /> },
          { path: 'recruiter/interviews', element: <InterviewEvaluationDetailPage /> },
          { path: 'recruiter/calendar/google/callback', element: <GoogleCalendarCallbackPage /> },

          { path: 'recruiter/job-offers', element: <JobOfferPage /> },
          { path: 'recruiter/analytics', element: <RecruiterAnalyticsPage /> },
          { path: 'recruiter/notifications', element: <RecruiterNotificationsPage /> },
        ],
      },
      {
        element: <RoleRoute allowedRoles={['interviewer']} />,
        children: [
          { path: 'interviewer', element: <InterviewerDashboardPage /> },
          { path: 'interviewer/applicants', element: <AssignedApplicantsPage /> },
          { path: 'interviewer/applicant-search', element: <RoleBasedApplicantSearchPage role="interviewer" /> },
          { path: 'interviewer/applicants/:applicationId', element: <ApplicantDetailPage /> },
          { path: 'interviewer/interviews', element: <InterviewListPage /> },
          { path: 'interviewer/interviews/:interviewId', element: <InterviewerInterviewDetailPage /> },
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
          {
            element: <HiringManagerOnboardingRoute />,
            children: [
              { path: 'hiring-manager/onboarding/organization', element: <OrganizationOnboardingPage /> },
              { path: 'hiring-manager/onboarding/subscription', element: <SubscriptionOnboardingPage /> },
              { path: 'hiring-manager', element: <HiringManagerDashboardPage /> },
              { path: 'hiring-manager/organization', element: <OrganizationProfilePage /> },
              { path: 'hiring-manager/team', element: <TeamMembersPage /> },
              { path: 'hiring-manager/team/create', element: <CreateTeamMemberPage /> },
              { path: 'hiring-manager/team/bulk-import', element: <BulkImportMembersPage /> },
              { path: 'hiring-manager/hiring-decisions', element: <PendingHiringDecisionsPage /> },
              { path: 'hiring-manager/applicant-search', element: <RoleBasedApplicantSearchPage role="hr_head" /> },
              { path: 'hiring-manager/job-requisitions', element: <HiringManagerJobRequisitionsPage /> },
              { path: 'hiring-manager/billing', element: <BillingPage /> },
              { path: 'hiring-manager/analytics', element: <HiringManagerAnalyticsPage /> },
              { path: 'hiring-manager/notifications', element: <NotificationsPage /> },
            ],
          },
        ],
      },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
], { basename: routerBasename });
