import RoleNav from '../../components/RoleNav.jsx';

const links = [
  { icon: 'dashboard', label: 'Dashboard', to: '/interviewer', end: true },
  { icon: 'candidates', label: 'Candidates', to: '/interviewer/candidates' },
  { icon: 'search', label: 'Candidate Search', to: '/interviewer/candidate-search' },
  { icon: 'interviews', label: 'Interviews', to: '/interviewer/interviews' },
  { icon: 'availability', label: 'Availability', to: '/interviewer/availability' },
  { icon: 'reports', label: 'Analytics', to: '/interviewer/analytics' },
  { icon: 'notifications', label: 'Notifications', to: '/interviewer/notifications' },
];

export default function InterviewerNav() {
  return <RoleNav items={links} />;
}
