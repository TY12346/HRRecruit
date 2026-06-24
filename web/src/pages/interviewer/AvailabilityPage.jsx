import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, CircularProgress, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import {
  createInterviewerAvailabilityPattern,
  createInterviewerUnavailableDate,
  deactivateInterviewerAvailabilityPattern,
  deleteInterviewerUnavailableDate,
  getInterviewerAvailabilityPatterns,
  getInterviewerUnavailableDates,
  updateInterviewerAvailabilityPattern,
} from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { getApiErrorMessage, titleize } from './interviewerUtils.js';

const days = [
  ['0', 'Monday'], ['1', 'Tuesday'], ['2', 'Wednesday'], ['3', 'Thursday'], ['4', 'Friday'], ['5', 'Saturday'], ['6', 'Sunday'],
];

const initialForm = {
  day_of_week: '0', start_time: '10:00', end_time: '12:00', slot_duration_minutes: 30,
  mode: 'online', meeting_link: '', location: '', effective_from: new Date().toISOString().slice(0, 10), effective_until: '',
};

export default function AvailabilityPage() {
  const [patterns, setPatterns] = useState([]);
  const [unavailableDates, setUnavailableDates] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [unavailableForm, setUnavailableForm] = useState({ date: '', reason: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const sortedPatterns = useMemo(() => [...patterns].sort((a, b) => a.day_of_week - b.day_of_week || a.start_time.localeCompare(b.start_time)), [patterns]);

  const loadAvailability = () => {
    setIsLoading(true);
    Promise.all([getInterviewerAvailabilityPatterns(), getInterviewerUnavailableDates()])
      .then(([patternData, unavailableData]) => {
        setPatterns(patternData);
        setUnavailableDates(unavailableData);
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load weekly availability.')))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => { loadAvailability(); }, []);

  const submit = async (event) => {
    event.preventDefault();
    setError(''); setSuccess(''); setIsSaving(true);
    const payload = { ...form, day_of_week: Number(form.day_of_week), slot_duration_minutes: Number(form.slot_duration_minutes), effective_until: form.effective_until || null };
    try {
      const saved = editingId ? await updateInterviewerAvailabilityPattern(editingId, payload) : await createInterviewerAvailabilityPattern(payload);
      setPatterns((current) => editingId ? current.map((item) => item.id === saved.id ? saved : item) : [...current, saved]);
      setForm(initialForm); setEditingId(null);
      setSuccess('Weekly availability saved. Applicants will see generated date/time slots from this pattern.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to save weekly availability.'));
    } finally { setIsSaving(false); }
  };

  const editPattern = (pattern) => {
    setEditingId(pattern.id);
    setForm({
      day_of_week: String(pattern.day_of_week), start_time: pattern.start_time?.slice(0, 5) ?? '', end_time: pattern.end_time?.slice(0, 5) ?? '',
      slot_duration_minutes: pattern.slot_duration_minutes, mode: pattern.mode, meeting_link: pattern.meeting_link ?? '', location: pattern.location ?? '',
      effective_from: pattern.effective_from, effective_until: pattern.effective_until ?? '',
    });
  };

  const deactivatePattern = async (patternId) => {
    const updated = await deactivateInterviewerAvailabilityPattern(patternId);
    setPatterns((current) => current.map((item) => item.id === patternId ? updated : item));
  };

  const addUnavailableDate = async (event) => {
    event.preventDefault();
    const created = await createInterviewerUnavailableDate(unavailableForm);
    setUnavailableDates((current) => [...current, created]);
    setUnavailableForm({ date: '', reason: '' });
  };

  const removeUnavailableDate = async (id) => {
    await deleteInterviewerUnavailableDate(id);
    setUnavailableDates((current) => current.filter((item) => item.id !== id));
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>My Weekly Availability</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Create reusable weekly patterns. The system generates real applicant-selectable dates and hides booked or unavailable dates.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        <Stack component="form" spacing={2} onSubmit={submit} sx={{ mb: 3 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField select label="Day of week" value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: e.target.value })} fullWidth>{days.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}</TextField>
            <TextField label="Start time" type="time" required value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} InputLabelProps={{ shrink: true }} fullWidth />
            <TextField label="End time" type="time" required value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} InputLabelProps={{ shrink: true }} fullWidth />
            <TextField label="Slot duration (minutes)" type="number" required value={form.slot_duration_minutes} onChange={(e) => setForm({ ...form, slot_duration_minutes: e.target.value })} fullWidth />
          </Stack>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField select label="Interview mode" value={form.mode} onChange={(e) => setForm({ ...form, mode: e.target.value })} fullWidth>{['online', 'physical', 'phone'].map((mode) => <MenuItem key={mode} value={mode}>{titleize(mode)}</MenuItem>)}</TextField>
            <TextField label="Meeting link" value={form.meeting_link} onChange={(e) => setForm({ ...form, meeting_link: e.target.value })} fullWidth />
            <TextField label="Physical location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} fullWidth />
          </Stack>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField label="Effective from" type="date" required value={form.effective_from} onChange={(e) => setForm({ ...form, effective_from: e.target.value })} InputLabelProps={{ shrink: true }} fullWidth />
            <TextField label="Effective until" type="date" value={form.effective_until} onChange={(e) => setForm({ ...form, effective_until: e.target.value })} InputLabelProps={{ shrink: true }} fullWidth />
          </Stack>
          <Button type="submit" variant="contained" disabled={isSaving}>{isSaving ? 'Saving…' : editingId ? 'Update weekly availability' : 'Save weekly availability'}</Button>
        </Stack>
        {isLoading ? <CircularProgress /> : null}
        <Stack spacing={2} sx={{ mb: 4 }}>
          {sortedPatterns.map((pattern) => <Card key={pattern.id} variant="outlined"><CardContent><Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}><Box><Typography variant="h6">Every {pattern.day_name}, {pattern.start_time} – {pattern.end_time}</Typography><Typography color="text.secondary">{pattern.slot_duration_minutes} min • {titleize(pattern.mode)} • {pattern.is_active ? 'Active' : 'Inactive'}</Typography><Typography color="text.secondary">Effective {pattern.effective_from}{pattern.effective_until ? ` until ${pattern.effective_until}` : ''}</Typography></Box><Stack direction="row" spacing={1}><Button variant="outlined" onClick={() => editPattern(pattern)}>Edit</Button><Button color="error" variant="outlined" disabled={!pattern.is_active} onClick={() => deactivatePattern(pattern.id)}>Deactivate</Button></Stack></Stack></CardContent></Card>)}
          {!isLoading && sortedPatterns.length === 0 ? <Typography color="text.secondary">No weekly availability patterns yet.</Typography> : null}
        </Stack>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>Unavailable dates</Typography>
        <Stack component="form" direction={{ xs: 'column', md: 'row' }} spacing={2} onSubmit={addUnavailableDate} sx={{ my: 2 }}>
          <TextField label="Unavailable date" type="date" required value={unavailableForm.date} onChange={(e) => setUnavailableForm({ ...unavailableForm, date: e.target.value })} InputLabelProps={{ shrink: true }} />
          <TextField label="Reason" value={unavailableForm.reason} onChange={(e) => setUnavailableForm({ ...unavailableForm, reason: e.target.value })} fullWidth />
          <Button type="submit" variant="outlined">Add</Button>
        </Stack>
        <Stack spacing={1}>{unavailableDates.map((item) => <Stack key={item.id} direction="row" justifyContent="space-between"><Typography>{item.date}{item.reason ? ` — ${item.reason}` : ''}</Typography><Button color="error" onClick={() => removeUnavailableDate(item.id)}>Remove</Button></Stack>)}</Stack>
      </Paper>
    </Box>
  );
}
