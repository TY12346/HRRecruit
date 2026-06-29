import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import App from './App.jsx';
import AppErrorBoundary from './AppErrorBoundary.jsx';
import './styles.css';

const plainBorder = '1px solid #777';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#000000' },
    secondary: { main: '#333333' },
    background: { default: '#ffffff', paper: '#ffffff' },
    text: { primary: '#000000', secondary: '#333333' },
  },
  typography: {
    fontFamily: 'Arial, Helvetica, sans-serif',
    h1: { fontWeight: 600 },
    h2: { fontWeight: 600 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 400 },
  },
  shape: { borderRadius: 0 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#ffffff',
          color: '#000000',
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          border: plainBorder,
          borderRadius: 0,
          boxShadow: 'none',
          color: '#000000',
          backgroundColor: '#eeeeee',
          padding: '4px 10px',
          minHeight: 'auto',
          minWidth: 'auto',
          '&:hover': {
            backgroundColor: '#dddddd',
            boxShadow: 'none',
          },
        },
        contained: {
          color: '#000000',
          backgroundColor: '#eeeeee',
          '&:hover': { backgroundColor: '#dddddd' },
        },
        outlined: {
          color: '#000000',
          border: plainBorder,
          backgroundColor: '#ffffff',
          '&:hover': { border: plainBorder, backgroundColor: '#eeeeee' },
        },
        text: {
          border: plainBorder,
          color: '#000000',
          backgroundColor: '#ffffff',
          '&:hover': { backgroundColor: '#eeeeee' },
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: plainBorder,
          borderRadius: 0,
          boxShadow: 'none',
          backgroundImage: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: plainBorder,
          borderRadius: 0,
          boxShadow: 'none',
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
          borderRadius: 0,
          backgroundColor: '#ffffff',
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#000000', borderWidth: 1 },
        },
        notchedOutline: { borderColor: '#777777' },
        input: { padding: '8px' },
      },
    },
    MuiInputLabel: {
      styleOverrides: { root: { color: '#000000' } },
    },
    MuiSelect: {
      defaultProps: { size: 'small' },
      styleOverrides: { select: { padding: '8px' } },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          border: plainBorder,
          borderRadius: 0,
          backgroundColor: '#f5f5f5',
          color: '#000000',
        },
        icon: { color: '#000000' },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          border: plainBorder,
          borderRadius: 0,
          backgroundColor: '#eeeeee',
          color: '#000000',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderBottom: plainBorder, padding: '6px 8px' },
        head: { fontWeight: 600, backgroundColor: '#eeeeee' },
      },
    },
    MuiDivider: {
      styleOverrides: { root: { borderColor: '#777777' } },
    },
    MuiCircularProgress: {
      styleOverrides: { root: { color: '#000000' } },
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
