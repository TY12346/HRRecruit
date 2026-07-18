import RoleNav from '../../components/RoleNav.jsx';

const recruiterLinks = [
  { icon: 'dashboard', label: 'Dashboard', to: '/recruiter', end: true },
  { icon: 'roles', label: 'Jobs', to: '/recruiter/jobs' },
  { icon: 'requisitions', label: 'Job Requisitions', to: '/recruiter/job-requisitions' },
  { icon: 'search', label: 'Candidate Search', to: '/recruiter/candidate-search' },
  { icon: 'interviews', label: 'Interviews', to: '/recruiter/interviews' },
  { icon: 'recommendations', label: 'Recommendations', to: '/recruiter/jobs' },
  { icon: 'offers', label: 'Offers', to: '/recruiter/job-offers' },
  { icon: 'reports', label: 'Analytics', to: '/recruiter/analytics' },
  { icon: 'notifications', label: 'Notifications', to: '/recruiter/notifications' },
];

export default function RecruiterNav() {
  return <RoleNav items={recruiterLinks} />;
}
