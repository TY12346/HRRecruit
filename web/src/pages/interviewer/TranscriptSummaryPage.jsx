import { useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Chip, Divider, List, ListItem, ListItemText, Paper, Stack, TextField, Typography } from '@mui/material';
import { useLocation, useParams } from 'react-router-dom';
import { generateTranscriptSummary, transcribeRecording, updateInterviewSummary } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { getApiErrorMessage, getStoredRecordingId, getStoredSummaryId, getStoredTranscriptId, setStoredSummaryId, setStoredTranscriptId } from './interviewerUtils.js';

const transparencyValue = (summary, key, fallback = '') => summary?.transparency?.[key] ?? summary?.summary_json?.[key] ?? fallback;

function SummaryTransparencyCard({ summary }) {
  if (!summary) return null;
  const provider = transparencyValue(summary, 'provider', 'unknown');
  const generationMode = transparencyValue(summary, 'generation_mode', 'unknown');
  const fallbackReason = transparencyValue(summary, 'fallback_reason', '');
  const model = transparencyValue(summary, 'model', '');
  const limitations = transparencyValue(summary, 'limitations', []);

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={1.5}>
          <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={1}>
            <Box>
              <Typography variant="h6">AI summary transparency</Typography>
              <Typography color="text.secondary">Shows how the summary was produced and why human review is required.</Typography>
            </Box>
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              <Chip label={`Provider: ${provider}`} color={provider === 'mock' ? 'default' : 'primary'} />
              <Chip label={generationMode.replaceAll('_', ' ')} />
            </Stack>
          </Stack>
          {model ? <Typography variant="body2"><strong>Model:</strong> {model}</Typography> : null}
          {fallbackReason ? <Alert severity="info">Fallback reason: {fallbackReason}</Alert> : null}
          <Alert severity="warning">{transparencyValue(summary, 'decision_boundary', 'This AI summary supports interviewer review only and must not be treated as a final hiring decision.')}</Alert>
          <Typography variant="subtitle2">Evidence excerpt used by AI</Typography>
          <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'grey.50' }}>
            <Typography variant="body2" whiteSpace="pre-line">{transparencyValue(summary, 'source_excerpt', 'No transcript excerpt available.')}</Typography>
          </Paper>
          <Typography variant="subtitle2">Known limitations</Typography>
          <List dense sx={{ listStyleType: 'disc', pl: 3 }}>
            {(Array.isArray(limitations) && limitations.length ? limitations : ['Interviewer must verify the summary against the transcript.']).map((item) => (
              <ListItem key={item} sx={{ display: 'list-item', p: 0 }}>
                <ListItemText primary={item} />
              </ListItem>
            ))}
          </List>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function TranscriptSummaryPage() {
  const { interviewId } = useParams();
  const location = useLocation();
  const [recordingId, setRecordingId] = useState(String(location.state?.recordingId ?? getStoredRecordingId(interviewId)));
  const [transcriptId, setTranscriptId] = useState(getStoredTranscriptId(interviewId));
  const [summaryId, setSummaryId] = useState(getStoredSummaryId(interviewId));
  const [transcript, setTranscript] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const makeTranscript = async () => {
    setError(''); setSuccess(''); setIsBusy(true);
    try {
      const data = await transcribeRecording(recordingId);
      setTranscript(data);
      setTranscriptId(String(data.id));
      setStoredTranscriptId(interviewId, data.id);
      setSuccess(data.transcript_json?.provider === 'mock' ? 'Mock transcript generated with provider metadata.' : 'Transcript generated with provider metadata.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to generate transcript.'));
    } finally {
      setIsBusy(false);
    }
  };

  const makeSummary = async () => {
    setError(''); setSuccess(''); setIsBusy(true);
    try {
      const data = await generateTranscriptSummary(transcriptId);
      setSummary(data);
      setSummaryId(String(data.id));
      setStoredSummaryId(interviewId, data.id);
      setSuccess('AI summary generated with transparency metadata. Please review and edit before using it in evaluation.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to generate AI summary.'));
    } finally {
      setIsBusy(false);
    }
  };

  const saveSummary = async () => {
    setError(''); setSuccess(''); setIsBusy(true);
    try {
      const editablePayload = {
        strengths: summary?.strengths ?? '',
        weaknesses: summary?.weaknesses ?? '',
        communication_score: summary?.communication_score ?? '',
        overall_impression: summary?.overall_impression ?? '',
        editable_summary_text: summary?.editable_summary_text ?? '',
      };
      const data = await updateInterviewSummary(summaryId, editablePayload);
      setSummary(data);
      setSuccess('AI summary edits saved. The transparency metadata remains available for audit/review.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to update AI summary.'));
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Transcript & AI Summary</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>Generate transcript and summary outputs, then verify AI-generated content before final evaluation.</Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        <Stack spacing={2}>
          <TextField label="Recording ID" value={recordingId} onChange={(event) => setRecordingId(event.target.value)} helperText="Auto-filled after upload on this browser; enter manually if needed." />
          <Button variant="contained" disabled={!recordingId || isBusy} onClick={makeTranscript}>Generate transcript</Button>
          {transcript ? (
            <Card variant="outlined">
              <CardContent>
                <Stack spacing={1}>
                  <Typography variant="h6">Transcript #{transcript.id}</Typography>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    <Chip label={`Provider: ${transcript.transcript_json?.provider ?? 'unknown'}`} />
                    {transcript.transcript_json?.fallback_reason ? <Chip label={`Fallback: ${transcript.transcript_json.fallback_reason}`} color="warning" /> : null}
                  </Stack>
                  <Typography whiteSpace="pre-line">{transcript.transcript_text}</Typography>
                </Stack>
              </CardContent>
            </Card>
          ) : null}
          <Divider />
          <TextField label="Transcript ID" value={transcriptId} onChange={(event) => setTranscriptId(event.target.value)} />
          <Button variant="contained" disabled={!transcriptId || isBusy} onClick={makeSummary}>Generate AI summary with transparency</Button>
          {summary ? (
            <Stack spacing={2}>
              <SummaryTransparencyCard summary={summary} />
              <Card variant="outlined">
                <CardContent>
                  <Stack spacing={2}>
                    <Alert severity="info">Edit the AI draft below. HRRecruit stores who edited it and blocks edits after final evaluation submission.</Alert>
                    <TextField label="Strengths" multiline minRows={2} value={summary.strengths ?? ''} onChange={(event) => setSummary({ ...summary, strengths: event.target.value })} />
                    <TextField label="Weaknesses" multiline minRows={2} value={summary.weaknesses ?? ''} onChange={(event) => setSummary({ ...summary, weaknesses: event.target.value })} />
                    <TextField label="Communication score" type="number" value={summary.communication_score ?? ''} onChange={(event) => setSummary({ ...summary, communication_score: event.target.value })} helperText="0-10 decision-support signal; verify against the transcript." />
                    <TextField label="Overall impression" multiline minRows={2} value={summary.overall_impression ?? ''} onChange={(event) => setSummary({ ...summary, overall_impression: event.target.value })} />
                    <TextField label="Editable summary text" multiline minRows={4} value={summary.editable_summary_text ?? ''} onChange={(event) => setSummary({ ...summary, editable_summary_text: event.target.value })} />
                    <Button variant="outlined" disabled={isBusy} onClick={saveSummary}>Save reviewed AI summary</Button>
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          ) : <TextField label="Summary ID" value={summaryId} onChange={(event) => setSummaryId(event.target.value)} helperText="Generate a new summary above to edit it in this page." />}
        </Stack>
      </Paper>
    </Box>
  );
}
