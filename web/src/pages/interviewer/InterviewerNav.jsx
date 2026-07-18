import RoleNav from '../../components/RoleNav.jsx';

const interviewerLinks = [
  { icon: 'dashboard', label: 'Dashboard', to: '/interviewer', end: true },
  { icon: 'roles', label: 'Open Roles', to: '/interviewer/candidate-search' },
  { icon: 'candidates', label: 'Candidates', to: '/interviewer/candidates' },
  { icon: 'interviews', label: 'Interviews', to: '/interviewer/interviews' },
  { icon: 'reports', label: 'Reports', to: '/interviewer/analytics' },
  { icon: 'settings', label: 'Settings', to: '/profile' },
];

export default function InterviewerNav() {
  return <RoleNav items={interviewerLinks} />;
}
