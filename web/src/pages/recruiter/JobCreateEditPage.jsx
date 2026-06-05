import { useEffect, useState } from 'react';
import { Alert, Box, Button, CircularProgress, FormControl, InputLabel, MenuItem, Paper, Select, Stack, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { createJob, getJob, updateJob } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';

const blankJob = { title: '', description: '', employment_type: 'full_time', approximate_salary: '', location: '', status: 'draft' };

export default function JobCreateEditPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(jobId);
  const [form, setForm] = useState(blankJob);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(isEdit);
  const [isSaving, setIsSaving] = useState(false);
  useEffect(() => { if (!isEdit) return; let active = true; getJob(jobId).then((job) => active && setForm({ title: job.title ?? '', description: job.description ?? '', employment_type: job.employment_type ?? '', approximate_salary: job.approximate_salary ?? '', location: job.location ?? '', status: job.status ?? 'draft' })).catch((err) => active && setError(getApiErrorMessage(err, 'Unable to load job.'))).finally(() => active && setIsLoading(false)); return () => { active = false; }; }, [isEdit, jobId]);
  const setField = (field) => (event) => setForm((current) => ({ ...current, [field]: event.target.value }));
  const handleSubmit = async (event) => { event.preventDefault(); setIsSaving(true); setError(''); try { const saved = isEdit ? await updateJob(jobId, form) : await createJob(form); navigate(`/recruiter/jobs/${saved.id}`); } catch (err) { setError(getApiErrorMessage(err, 'Unable to save job.')); } finally { setIsSaving(false); } };
  return <Box><RecruiterNav /><Paper component="form" onSubmit={handleSubmit} sx={{ p: 3 }}><Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>{isEdit ? 'Edit job' : 'Create job'}</Typography><Typography color="text.secondary" sx={{ mb: 2 }}>Keep content practical for the FYP demo and publish when requirements are ready.</Typography>{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{isLoading ? <CircularProgress /> : <Stack spacing={2}><TextField label="Job title" required value={form.title} onChange={setField('title')} /><TextField label="Description" required multiline minRows={5} value={form.description} onChange={setField('description')} /><Stack direction={{ xs: 'column', md: 'row' }} spacing={2}><TextField label="Employment type" required value={form.employment_type} onChange={setField('employment_type')} /><TextField label="Approximate salary" required type="number" value={form.approximate_salary} onChange={setField('approximate_salary')} /><TextField label="Location" required value={form.location} onChange={setField('location')} /><FormControl><InputLabel>Status</InputLabel><Select label="Status" value={form.status} onChange={setField('status')}><MenuItem value="draft">Draft</MenuItem><MenuItem value="open">Open</MenuItem><MenuItem value="closed">Closed</MenuItem></Select></FormControl></Stack><Stack direction="row" spacing={1}><Button disabled={isSaving} type="submit" variant="contained">{isSaving ? 'Saving…' : 'Save job'}</Button><Button onClick={() => navigate(-1)} variant="outlined">Cancel</Button></Stack></Stack>}</Paper></Box>;
}
