import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import App from './App.jsx';
import AppErrorBoundary from './AppErrorBoundary.jsx';
import './styles.css';

const border = '1px solid #bfdbfe';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#2563eb', dark: '#1d4ed8', light: '#dbeafe', contrastText: '#ffffff' },
    secondary: { main: '#0ea5e9', dark: '#0284c7', light: '#e0f2fe', contrastText: '#ffffff' },
    background: { default: '#eff6ff', paper: '#ffffff' },
    text: { primary: '#172554', secondary: '#475569' },
  },
  typography: {
    fontFamily: 'Inter, Arial, Helvetica, sans-serif',
    h1: { fontWeight: 600 },
    h2: { fontWeight: 600 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 10 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#eff6ff',
          color: '#172554',
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          padding: '7px 14px',
          minHeight: 'auto',
          minWidth: 'auto',
          '&:hover': { boxShadow: 'none' },
        },
        contained: {
          color: '#ffffff',
          backgroundColor: '#2563eb',
          '&:hover': { backgroundColor: '#1d4ed8' },
        },
        outlined: {
          color: '#1d4ed8',
          border: border,
          backgroundColor: '#ffffff',
          '&:hover': { border: '1px solid #2563eb', backgroundColor: '#eff6ff' },
        },
        text: {
          color: '#1d4ed8',
          backgroundColor: 'transparent',
          '&:hover': { backgroundColor: '#dbeafe' },
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: border,
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(30, 64, 175, 0.08)',
          backgroundImage: 'none',
        },
        outlined: {
          border: border,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: border,
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(30, 64, 175, 0.08)',
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: '12px',
          '&:last-child': { paddingBottom: '12px' },
        },
      },
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined', size: 'small' },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          backgroundColor: '#ffffff',
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#2563eb', borderWidth: 2 },
        },
        notchedOutline: { borderColor: '#93c5fd' },
        input: { padding: '8px' },
      },
    },
    MuiInputLabel: {
      styleOverrides: { root: { color: '#1e3a8a' } },
    },
    MuiSelect: {
      defaultProps: { size: 'small' },
      styleOverrides: { select: { padding: '8px' } },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          border: border,
          borderRadius: 8,
          backgroundColor: '#eff6ff',
          color: '#172554',
        },
        icon: { color: '#2563eb' },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          border: border,
          borderRadius: 16,
          backgroundColor: '#dbeafe',
          color: '#1e40af',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderBottom: border, padding: '10px 12px' },
        head: { fontWeight: 700, backgroundColor: '#dbeafe', color: '#1e3a8a' },
      },
    },
    MuiDivider: {
      styleOverrides: { root: { borderColor: '#bfdbfe' } },
    },
    MuiCircularProgress: {
      styleOverrides: { root: { color: '#2563eb' } },
    },
  },
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppErrorBoundary>
        <App />
      </AppErrorBoundary>
    </ThemeProvider>
  </StrictMode>,
);
