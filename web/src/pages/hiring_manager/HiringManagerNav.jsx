import RoleNav from '../../components/RoleNav.jsx';

const navItems = [
  { icon: 'dashboard', label: 'Dashboard', to: '/hiring-manager', end: true },
  { icon: 'decisions', label: 'Hiring Decisions', to: '/hiring-manager/hiring-decisions' },
  { icon: 'search', label: 'Applicant Search', to: '/hiring-manager/applicant-search' },
  { icon: 'requisitions', label: 'Job Requisitions', to: '/hiring-manager/job-requisitions' },
  { icon: 'reports', label: 'Analytics', to: '/hiring-manager/analytics' },
  { icon: 'team', label: 'Recruiter & Interviewer', to: '/hiring-manager/team' },
  { icon: 'organization', label: 'Organization Account', to: '/hiring-manager/organization' },
  { icon: 'billing', label: 'Billing', to: '/hiring-manager/billing' },
  { icon: 'notifications', label: 'Notifications', to: '/hiring-manager/notifications' },
];

export default function HiringManagerNav() {
  return <RoleNav items={navItems} />;
}
