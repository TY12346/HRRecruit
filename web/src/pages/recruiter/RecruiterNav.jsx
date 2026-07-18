import RoleNav from '../../components/RoleNav.jsx';

const recruiterLinks = [
  { icon: 'dashboard', label: 'Dashboard', to: '/recruiter', end: true },
  { icon: 'roles', label: 'Open Roles', to: '/recruiter/jobs' },
  { icon: 'candidates', label: 'Candidates', to: '/recruiter/applications' },
  { icon: 'interviews', label: 'Interviews', to: '/recruiter/interviews' },
  { icon: 'reports', label: 'Reports', to: '/recruiter/analytics' },
  { icon: 'settings', label: 'Settings', to: '/profile' },
];

export default function RecruiterNav() {
  return <RoleNav items={recruiterLinks} />;
}
