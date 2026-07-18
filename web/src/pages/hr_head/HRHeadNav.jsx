import RoleNav from '../../components/RoleNav.jsx';

const hrHeadLinks = [
  { icon: 'dashboard', label: 'Dashboard', to: '/hr-head', end: true },
  { icon: 'roles', label: 'Open Roles', to: '/hr-head/job-requisitions' },
  { icon: 'candidates', label: 'Candidates', to: '/hr-head/applicant-search' },
  { icon: 'interviews', label: 'Interviews', to: '/hr-head/hiring-decisions' },
  { icon: 'reports', label: 'Reports', to: '/hr-head/analytics' },
  { icon: 'settings', label: 'Settings', to: '/hr-head/organization' },
];

export default function HRHeadNav() {
  return <RoleNav items={hrHeadLinks} />;
}
