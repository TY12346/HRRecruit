import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, CircularProgress, Paper, Stack, TextField, Typography } from '@mui/material';
import { cancelInterviewerAvailabilitySlot, createInterviewerAvailabilitySlot, getInterviewerAvailabilitySlots } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { formatDateTime, getApiErrorMessage, titleize } from './interviewerUtils.js';

const initialForm = {
  start_datetime: '',
  end_datetime: '',
};

export default function AvailabilityPage() {
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const sortedSlots = useMemo(
    () => [...slots].sort((a, b) => new Date(a.start_datetime) - new Date(b.start_datetime)),
    [slots],
  );

  const loadSlots = () => {
    setIsLoading(true);
    getInterviewerAvailabilitySlots()
      .then(setSlots)
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load availability slots.')))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadSlots();
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setIsSaving(true);
    try {
      const created = await createInterviewerAvailabilitySlot({
        start_datetime: form.start_datetime,
        end_datetime: form.end_datetime,
      });
      setSlots((current) => [...current, created]);
      setForm(initialForm);
      setSuccess('Availability slot added. Recruiters can now include this slot in self-scheduling requests.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to add availability slot.'));
    } finally {
      setIsSaving(false);
    }
  };

  const cancelSlot = async (slotId) => {
    setError('');
    setSuccess('');
    try {
      const updated = await cancelInterviewerAvailabilitySlot(slotId);
      setSlots((current) => current.map((slot) => (slot.id === slotId ? updated : slot)));
      setSuccess('Availability slot cancelled.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to cancel availability slot.'));
    }
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Availability</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Publish interview time slots for applicant self-scheduling. Booked slots cannot be cancelled from this page.
        </Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        <Stack component="form" spacing={2} onSubmit={submit} sx={{ mb: 3 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="Start date/time"
              type="datetime-local"
              required
              value={form.start_datetime}
              onChange={(event) => setForm({ ...form, start_datetime: event.target.value })}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
            <TextField
              label="End date/time"
              type="datetime-local"
              required
              value={form.end_datetime}
              onChange={(event) => setForm({ ...form, end_datetime: event.target.value })}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
          </Stack>
          <Button type="submit" variant="contained" disabled={isSaving}>{isSaving ? 'Adding…' : 'Add availability slot'}</Button>
        </Stack>
        {isLoading ? <CircularProgress /> : null}
        <Stack spacing={2}>
          {sortedSlots.map((slot) => (
            <Card key={slot.id} variant="outlined">
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
                  <Box>
                    <Typography variant="h6">{formatDateTime(slot.start_datetime)} – {formatDateTime(slot.end_datetime)}</Typography>
                    <Typography color="text.secondary">Status: {titleize(slot.status)}</Typography>
                  </Box>
                  <Button
                    color="error"
                    disabled={slot.status !== 'available'}
                    onClick={() => cancelSlot(slot.id)}
                    variant="outlined"
                  >
                    Cancel slot
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          ))}
          {!isLoading && sortedSlots.length === 0 ? <Typography color="text.secondary">No availability slots yet.</Typography> : null}
        </Stack>
      </Paper>
    </Box>
  );
}
