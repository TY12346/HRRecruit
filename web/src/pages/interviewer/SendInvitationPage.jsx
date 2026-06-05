import { useEffect, useState } from 'react';
import { Alert, Box, Button, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { getInterview, sendInterviewInvitation } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { candidateName, formatDateInput, formatDateTime, getApiErrorMessage, jobTitle, latestInviteStatus } from './interviewerUtils.js';

export default function SendInvitationPage() {
  const { interviewId } = useParams();
  const navigate = useNavigate();
  const [interview, setInterview] = useState(null);
  const [form, setForm] = useState({ proposed_datetime: '', mode: 'online', meeting_link: '', location: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => { getInterview(interviewId).then((data) => { setInterview(data); setForm((current) => ({ ...current, proposed_datetime: formatDateInput(data.latest_invitation?.proposed_datetime), mode: data.latest_invitation?.mode ?? 'online', meeting_link: data.latest_invitation?.meeting_link ?? data.meeting_link ?? '', location: data.latest_invitation?.location ?? data.location ?? '' })); }).catch((err) => setError(getApiErrorMessage(err, 'Unable to load interview.'))); }, [interviewId]);

  const submit = async (event) => {
    event.preventDefault(); setError(''); setSuccess(''); setIsSaving(true);
    try {
      const payload = { ...form, proposed_datetime: new Date(form.proposed_datetime).toISOString() };
      await sendInterviewInvitation(interviewId, payload);
      setSuccess('Interview invitation sent.');
      const updated = await getInterview(interviewId);
      setInterview(updated);
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to send invitation.')); } finally { setIsSaving(false); }
  };

  return <Box><InterviewerNav /><Paper sx={{ p: 3 }}><Typography variant="h5" sx={{ fontWeight: 700 }}>Send Interview Invitation</Typography>{interview ? <Typography color="text.secondary" sx={{ mb: 2 }}>{candidateName(interview)} • {jobTitle(interview)} • Current response: {latestInviteStatus(interview)} {interview.latest_invitation?.responded_at ? `at ${formatDateTime(interview.latest_invitation.responded_at)}` : ''}</Typography> : null}{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}<Stack component="form" spacing={2} onSubmit={submit}><TextField label="Proposed date/time" type="datetime-local" required value={form.proposed_datetime} onChange={(event) => setForm({ ...form, proposed_datetime: event.target.value })} InputLabelProps={{ shrink: true }} /><TextField select label="Mode" value={form.mode} onChange={(event) => setForm({ ...form, mode: event.target.value })}><MenuItem value="online">Online</MenuItem><MenuItem value="physical">Physical</MenuItem><MenuItem value="phone">Phone</MenuItem></TextField><TextField label="Meeting link" value={form.meeting_link} onChange={(event) => setForm({ ...form, meeting_link: event.target.value })} helperText="Required for online interviews." /><TextField label="Physical location" value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} helperText="Required for physical interviews." /><Stack direction="row" spacing={1}><Button type="submit" variant="contained" disabled={isSaving}>{isSaving ? 'Sending…' : 'Send invitation'}</Button><Button variant="outlined" onClick={() => navigate(`/interviewer/interviews/${interviewId}`)}>Back to detail</Button></Stack></Stack></Paper></Box>;
}
