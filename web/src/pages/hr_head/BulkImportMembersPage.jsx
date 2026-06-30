import { useState } from 'react';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import { Alert, Box, Button, List, ListItem, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { bulkImportOrganizationMembers } from '../../api/client.js';
import HRHeadNav from './HRHeadNav.jsx';
import { getApiErrorMessage } from './hrHeadUtils.js';

const REQUIRED_HEADERS = ['email', 'full_name', 'role'];
const OPTIONAL_HEADERS = ['phone_number'];
const SUPPORTED_EXTENSIONS = ['csv', 'xlsx', 'xls'];

function extensionFor(file) {
  return file?.name?.split('.').pop()?.toLowerCase() ?? '';
}

function normalizeRows(rows) {
  return rows
    .map((row) => {
      const normalized = {};
      Object.entries(row ?? {}).forEach(([key, value]) => {
        normalized[String(key).trim().toLowerCase()] = typeof value === 'string' ? value.trim() : value;
      });
      return {
        email: normalized.email ?? '',
        full_name: normalized.full_name ?? '',
        phone_number: normalized.phone_number ?? '',
        role: normalized.role ?? '',
      };
    })
    .filter((row) => Object.values(row).some((value) => String(value ?? '').trim()));
}

function validateHeaders(rows) {
  if (!rows.length) return 'The selected file does not contain any team-member rows.';
  const availableHeaders = new Set(Object.keys(rows[0] ?? {}).map((header) => header.trim().toLowerCase()));
  const missingHeaders = REQUIRED_HEADERS.filter((header) => !availableHeaders.has(header));
  if (missingHeaders.length) {
    return `Missing required column(s): ${missingHeaders.join(', ')}.`;
  }
  return '';
}

function parseCsvWithPapa(file) {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: 'greedy',
      complete: ({ data, errors }) => {
        if (errors?.length) {
          reject(new Error(errors.map((error) => `Row ${error.row ?? '?'}: ${error.message}`).join('; ')));
          return;
        }
        resolve(data);
      },
      error: (error) => reject(error),
    });
  });
}

async function parseWorkbookWithSheetJS(file) {
  const workbook = XLSX.read(await file.arrayBuffer(), { type: 'array' });
  const firstSheetName = workbook.SheetNames[0];
  if (!firstSheetName) {
    throw new Error('The selected Excel workbook does not contain any worksheets.');
  }
  return XLSX.utils.sheet_to_json(workbook.Sheets[firstSheetName], { defval: '' });
}

async function parseMembersFile(file) {
  const extension = extensionFor(file);
  if (!SUPPORTED_EXTENSIONS.includes(extension)) {
    throw new Error('Choose a CSV, XLSX, or XLS file.');
  }
  const rawRows = extension === 'csv' ? await parseCsvWithPapa(file) : await parseWorkbookWithSheetJS(file);
  const headerError = validateHeaders(rawRows);
  if (headerError) throw new Error(headerError);
  return normalizeRows(rawRows);
}

export default function BulkImportMembersPage() {
  const [importFile, setImportFile] = useState(null);
  const [parsedMembers, setParsedMembers] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [isParsing, setIsParsing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0] ?? null;
    setImportFile(file);
    setParsedMembers([]);
    setResult(null);
    setError('');
    if (!file) return;

    setIsParsing(true);
    try {
      const rows = await parseMembersFile(file);
      setParsedMembers(rows);
    } catch (parseError) {
      setError(parseError.message || 'Unable to parse the selected spreadsheet.');
    } finally {
      setIsParsing(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!parsedMembers.length) {
      setError('Choose and parse a CSV/XLSX/XLS file before importing.');
      return;
    }

    setError('');
    setResult(null);
    setIsSubmitting(true);
    try {
      const data = await bulkImportOrganizationMembers(parsedMembers);
      setResult(data);
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, 'Unable to import team members.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box>
      <HRHeadNav />
      <Paper sx={{ p: 3 }}>
        <Typography component="h2" variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
          Bulk Import Members
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Upload a CSV or Excel spreadsheet with headers: {REQUIRED_HEADERS.join(', ')}, and optional {OPTIONAL_HEADERS.join(', ')}. CSV files are parsed with PapaParse; Excel files are parsed with SheetJS before sending rows to the API.
        </Typography>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {parsedMembers.length ? (
          <Alert severity="info" sx={{ mb: 2 }}>
            Parsed {parsedMembers.length} row(s) from {importFile?.name}. Review the preview, then import.
          </Alert>
        ) : null}
        {result ? (
          <Alert severity={result.errors?.length ? 'warning' : 'success'} sx={{ mb: 2 }}>
            Created {result.created?.length ?? 0} members. {result.errors?.length ?? 0} rows had errors.
          </Alert>
        ) : null}

        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <Button component="label" variant="outlined">
              {importFile ? importFile.name : 'Choose CSV / Excel file'}
              <input hidden accept=".csv,.xlsx,.xls,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel" type="file" onChange={handleFileChange} />
            </Button>
            <Stack direction="row" spacing={1}>
              <Button disabled={isParsing || isSubmitting || !parsedMembers.length} type="submit" variant="contained">
                {isParsing ? 'Parsing…' : isSubmitting ? 'Importing…' : 'Import members'}
              </Button>
              <Button component={RouterLink} to="/hr-head/team" variant="outlined">
                Back to team
              </Button>
            </Stack>
          </Stack>
        </Box>

        {parsedMembers.length ? (
          <Box sx={{ mt: 3 }}>
            <Typography component="h3" variant="h6">Preview parsed rows</Typography>
            <List dense>
              {parsedMembers.slice(0, 8).map((member, index) => (
                <ListItem key={`${member.email}-${index}`}>
                  Row {index + 2}: {member.full_name || '(missing name)'} — {member.email || '(missing email)'} ({member.role || 'missing role'})
                </ListItem>
              ))}
            </List>
            {parsedMembers.length > 8 ? <Typography color="text.secondary">Showing first 8 rows only.</Typography> : null}
          </Box>
        ) : null}

        {result?.created?.length ? (
          <Box sx={{ mt: 3 }}>
            <Typography component="h3" variant="h6">Created members</Typography>
            <List dense>
              {result.created.map((member) => (
                <ListItem key={member.id}>{member.full_name} — {member.email} ({member.role})</ListItem>
              ))}
            </List>
          </Box>
        ) : null}

        {result?.errors?.length ? (
          <Box sx={{ mt: 3 }}>
            <Typography component="h3" variant="h6">Rows needing attention</Typography>
            <List dense>
              {result.errors.map((rowError) => (
                <ListItem key={rowError.row}>Row {rowError.row}: {JSON.stringify(rowError.errors)}</ListItem>
              ))}
            </List>
          </Box>
        ) : null}
      </Paper>
    </Box>
  );
}
