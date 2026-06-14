import { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { deleteJob, duplicateJob, getJobs } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './recruiterUtils.js';

export default function JobListPage() {
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const loadJobs = async () => { setIsLoading(true); setError(''); try { setJobs(await getJobs()); } catch (err) { setError(getApiErrorMessage(err, 'Unable to load jobs.')); } finally { setIsLoading(false); } };
  useEffect(() => { let active = true; getJobs().then((data) => { if (active) setJobs(data); }).catch((err) => { if (active) setError(getApiErrorMessage(err, 'Unable to load jobs.')); }).finally(() => { if (active) setIsLoading(false); }); return () => { active = false; }; }, []);
  const handleDelete = async (job) => { if (!window.confirm(`Delete ${job.title}?`)) return; try { await deleteJob(job.id); setSuccess('Job deleted.'); loadJobs(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to delete job.')); } };
  const handleDuplicate = async (job) => { try { const copy = await duplicateJob(job.id); setSuccess(`Duplicated as ${copy.title}.`); loadJobs(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to duplicate job.')); } };
  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}><Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 2 }}><Box><Typography variant="h5" sx={{ fontWeight: 700 }}>Jobs</Typography></Box><Button component={RouterLink} to="/recruiter/jobs/create" variant="contained">Create job</Button></Stack>{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}{isLoading ? <CircularProgress /> : null}<Table><TableHead><TableRow><TableCell>Title</TableCell><TableCell>Status</TableCell><TableCell>Type</TableCell><TableCell>Location</TableCell><TableCell>Salary</TableCell><TableCell>Created</TableCell><TableCell align="right">Actions</TableCell></TableRow></TableHead><TableBody>{jobs.map((job) => <TableRow key={job.id}><TableCell><Button component={RouterLink} to={`/recruiter/jobs/${job.id}`}>{job.title}</Button></TableCell><TableCell><Chip label={titleize(job.status)} size="small" color={job.status === 'open' ? 'success' : 'default'} /></TableCell><TableCell>{job.employment_type}</TableCell><TableCell>{job.location}</TableCell><TableCell>{job.approximate_salary}</TableCell><TableCell>{formatDateTime(job.created_at)}</TableCell><TableCell align="right"><Stack direction="row" spacing={1} justifyContent="flex-end"><Button component={RouterLink} to={`/recruiter/jobs/${job.id}/edit`} size="small">Edit</Button><Button onClick={() => handleDuplicate(job)} size="small">Duplicate</Button><Button color="error" onClick={() => handleDelete(job)} size="small">Delete</Button></Stack></TableCell></TableRow>)}{!isLoading && jobs.length === 0 ? <TableRow><TableCell colSpan={7}>No jobs yet.</TableCell></TableRow> : null}</TableBody></Table></Paper></Box>;
}
