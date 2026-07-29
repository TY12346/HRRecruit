import { Badge, Box, Button, Stack } from '@mui/material';
import { NavLink } from 'react-router-dom';
import { useNotifications } from '../notifications/NotificationContext.jsx';

const iconProps = {
  fill: 'none',
  height: 24,
  stroke: 'currentColor',
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  strokeWidth: 2,
  viewBox: '0 0 24 24',
  width: 24,
};

function DashboardIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <rect x="4" y="4" width="6" height="6" rx="1" />
      <rect x="14" y="4" width="6" height="6" rx="1" />
      <rect x="4" y="14" width="6" height="6" rx="1" />
      <rect x="14" y="14" width="6" height="6" rx="1" />
    </svg>
  );
}

function BriefcaseIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <path d="M9 6V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1" />
      <rect x="3" y="6" width="18" height="14" rx="2" />
      <path d="M8 6v14M16 6v14" />
    </svg>
  );
}

function ApplicantsIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 19a5.5 5.5 0 0 1 11 0" />
      <path d="M16 5.5a3 3 0 0 1 0 5" />
      <path d="M18 14a5 5 0 0 1 2.5 4.5" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M8 3v4M16 3v4M3 10h18" />
      <circle cx="15" cy="15" r="3" />
      <path d="M15 13.5V15l1 1" />
    </svg>
  );
}

function InterviewIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <rect x="3" y="6" width="13" height="12" rx="2" />
      <path d="m16 10 5-3v10l-5-3" />
      <circle cx="9.5" cy="12" r="2.5" />
    </svg>
  );
}

function ReportsIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <path d="M4 20V5" />
      <path d="M4 20h16" />
      <path d="M8 16V9" />
      <path d="M12 16V4" />
      <path d="M16 16v-5" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.1 2.1-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-3v-.2a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L6.6 17l.1-.1A1.7 1.7 0 0 0 7 15a1.7 1.7 0 0 0-1.6-1H5.2v-3h.2A1.7 1.7 0 0 0 7 10a1.7 1.7 0 0 0-.3-1.9l-.1-.1 2.1-2.1.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6v-.2h3v.2a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 8l-.1.1A1.7 1.7 0 0 0 19.4 10a1.7 1.7 0 0 0 1.6 1h.2v3H21a1.7 1.7 0 0 0-1.6 1Z" />
    </svg>
  );
}

function NotificationIcon() {
  return (
    <svg aria-hidden="true" {...iconProps}>
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
      <path d="M10 21h4" />
    </svg>
  );
}

const icons = {
  availability: <CalendarIcon />,
  billing: <BriefcaseIcon />,
  applicants: <ApplicantsIcon />,
  dashboard: <DashboardIcon />,
  interviews: <InterviewIcon />,
  notifications: <NotificationIcon />,
  offers: <BriefcaseIcon />,
  organization: <SettingsIcon />,
  decisions: <ApplicantsIcon />,
  reports: <ReportsIcon />,
  requisitions: <BriefcaseIcon />,
  roles: <BriefcaseIcon />,
  search: <ApplicantsIcon />,
  settings: <SettingsIcon />,
  team: <ApplicantsIcon />,
};

export default function RoleNav({ items }) {
  const { unreadCount } = useNotifications();
  return (
    <Box
      component="nav"
      sx={{
        bgcolor: '#ffffff',
        borderRight: { md: '1px solid #bfdbfe' },
        bottom: { md: 0 },
        left: { md: 0 },
        mb: { xs: 4, md: 0 },
        overflowY: { md: 'auto' },
        px: { xs: 1, md: 1.25 },
        py: { xs: 1, md: 2.25 },
        position: { xs: 'static', md: 'fixed' },
        top: { md: 64 },
        width: { md: 370 },
        zIndex: (theme) => theme.zIndex.drawer,
      }}
    >
      <Stack direction={{ xs: 'row', md: 'column' }} spacing={2.25} useFlexGap flexWrap={{ xs: 'wrap', md: 'nowrap' }}>
        {items.map((item) => (
          <Button
            component={NavLink}
            end={item.end}
            key={item.to}
            to={item.to}
            sx={{
              borderRadius: '16px',
              color: '#475569',
              fontSize: 22,
              fontWeight: 500,
              gap: 2.25,
              justifyContent: { xs: 'center', md: 'flex-start' },
              lineHeight: 1.2,
              minHeight: 56,
              px: 2.25,
              textTransform: 'none',
              width: { xs: 'auto', md: '100%' },
              '& .role-nav-icon': {
                alignItems: 'center',
                color: '#2563eb',
                display: 'inline-flex',
                flex: '0 0 28px',
                justifyContent: 'center',
              },
              '&.active': {
                bgcolor: '#dbeafe',
                color: '#1d4ed8',
              },
              '&.active .role-nav-icon': {
                color: '#1d4ed8',
              },
              '&:hover': {
                bgcolor: '#eff6ff',
              },
            }}
          >
            <Badge
              color="error"
              invisible={item.icon !== 'notifications' || unreadCount === 0}
              overlap="circular"
              variant="dot"
            >
              <Box className="role-nav-icon" component="span">{icons[item.icon] ?? item.icon}</Box>
            </Badge>
            {item.label}
          </Button>
        ))}
      </Stack>
    </Box>
  );
}
