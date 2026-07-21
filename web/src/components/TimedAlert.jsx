import { useEffect, useState } from 'react';
import { Alert as MuiAlert, Button, Snackbar } from '@mui/material';

const AUTO_HIDE_DURATION = 5000;

/**
 * Displays success and error feedback as a temporary, dismissible notification.
 * Other alert severities retain their normal inline rendering for contextual guidance.
 */
export default function TimedAlert({ children, severity = 'success', sx, ...alertProps }) {
  const isToast = severity === 'success' || severity === 'error';
  const [open, setOpen] = useState(isToast);

  useEffect(() => {
    if (isToast) {
      setOpen(true);
    }
  }, [children, isToast, severity]);

  if (!isToast) {
    return <MuiAlert severity={severity} sx={sx} {...alertProps}>{children}</MuiAlert>;
  }

  const dismiss = () => setOpen(false);

  return (
    <Snackbar
      anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      autoHideDuration={AUTO_HIDE_DURATION}
      onClose={(_, reason) => {
        if (reason !== 'clickaway') dismiss();
      }}
      open={open}
    >
      <MuiAlert
        action={<Button color="inherit" onClick={dismiss} size="small">Dismiss</Button>}
        severity={severity}
        sx={{ alignItems: 'center', ...sx }}
        variant="filled"
        {...alertProps}
      >
        {children}
      </MuiAlert>
    </Snackbar>
  );
}
