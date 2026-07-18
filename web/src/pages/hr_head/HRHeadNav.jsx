import RoleNav from '../../components/RoleNav.jsx';

const navItems = [
  { icon: 'dashboard', label: 'Dashboard', to: '/hr-head', end: true },
  { icon: 'recommendations', label: 'Hiring Recommendations', to: '/hr-head/hiring-decisions' },
  { icon: 'search', label: 'Applicant Search', to: '/hr-head/applicant-search' },
  { icon: 'requisitions', label: 'Job Requisitions', to: '/hr-head/job-requisitions' },
  { icon: 'reports', label: 'Analytics', to: '/hr-head/analytics' },
  { icon: 'team', label: 'Recruiter & Interviewer', to: '/hr-head/team' },
  { icon: 'organization', label: 'Organization Account', to: '/hr-head/organization' },
  { icon: 'billing', label: 'Billing', to: '/hr-head/billing' },
  { icon: 'notifications', label: 'Notifications', to: '/hr-head/notifications' },
];

export default function HRHeadNav() {
  return <RoleNav items={navItems} />;
}
