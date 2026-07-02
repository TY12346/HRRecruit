import { Alert, Box, Chip, Stack, Typography } from '@mui/material';
import { APPLICATION_PHASES, getApplicationPhaseIndex, getApplicationStatusInfo } from '../utils/recruitmentFlow.js';

export default function ApplicationFlowSummary({ status, role = 'recruiter', compact = false }) {
  const currentIndex = getApplicationPhaseIndex(status);
  const info = getApplicationStatusInfo(status, role);
  const isClosed = ['rejected', 'withdrawn', 'offer_declined'].includes(status);

  return (
    <Alert severity={isClosed ? 'warning' : 'info'} sx={{ alignItems: 'flex-start' }}>
      <Stack spacing={compact ? 1 : 1.5}>
        <Box>
          <Typography variant="subtitle2">Current stage: {info.label}</Typography>
          <Typography variant="body2">{info.description}</Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}><strong>Next action:</strong> {info.nextAction}</Typography>
        </Box>
        {!compact ? (
          <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
            {APPLICATION_PHASES.map((phase, index) => (
              <Chip
                key={phase.key}
                label={phase.label}
                size="small"
                color={index === currentIndex ? 'primary' : index < currentIndex ? 'success' : 'default'}
                variant={index <= currentIndex ? 'filled' : 'outlined'}
              />
            ))}
          </Stack>
        ) : null}
      </Stack>
    </Alert>
  );
}
