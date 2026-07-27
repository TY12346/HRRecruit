import RoleNav from '../../components/RoleNav.jsx';

const links = [
  { icon: 'applicants', label: 'Applicants', to: '/interviewer/applicants' },
  { icon: 'search', label: 'Applicant Search', to: '/interviewer/applicant-search' },
  { icon: 'interviews', label: 'Interviews', to: '/interviewer/interviews' },
  { icon: 'availability', label: 'Availability', to: '/interviewer/availability' },
  { icon: 'reports', label: 'Analytics', to: '/interviewer/analytics' },
  { icon: 'notifications', label: 'Notifications', to: '/interviewer/notifications' },
];

export default function InterviewerNav() {
  return <RoleNav items={links} />;
}
