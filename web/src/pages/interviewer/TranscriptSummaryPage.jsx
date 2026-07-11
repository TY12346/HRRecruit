import { useState } from 'react';
import { Alert, Box, Button, Paper, Stack, Typography } from '@mui/material';
import { useLocation, useParams } from 'react-router-dom';
import { transcribeRecording, uploadInterviewRecording } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { getApiErrorMessage, getStoredRecordingId, setStoredRecordingId, setStoredTranscriptId } from './interviewerUtils.js';

function TranscriptResult({ transcript }) {
  if (!transcript) return null;
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
        Generated transcript
      </Typography>
      <Typography variant="body1" whiteSpace="pre-line">
        {transcript.transcript_text || 'No transcript text returned.'}
      </Typography>
    </Paper>
  );
}

export default function TranscriptSummaryPage() {
  const { interviewId } = useParams();
  const location = useLocation();
  const [recordingId, setRecordingId] = useState(String(location.state?.recordingId ?? getStoredRecordingId(interviewId) ?? ''));
  const [file, setFile] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const generateTranscript = async () => {
    setError('');
    setSuccess('');
    setIsBusy(true);
    try {
      let activeRecordingId = recordingId;
      if (file) {
        const recording = await uploadInterviewRecording(interviewId, file);
        activeRecordingId = String(recording.id);
        setRecordingId(activeRecordingId);
        setStoredRecordingId(interviewId, recording.id);
      }
      if (!activeRecordingId) {
        setError('Choose an audio file before generating the transcript.');
        return;
      }
      const data = await transcribeRecording(activeRecordingId);
      setTranscript(data);
      setStoredTranscriptId(interviewId, data.id);
      setSuccess('Transcript generated successfully.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to generate transcript.'));
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <Box>
      <InterviewerNav />
      <Paper sx={{ p: 3 }}>
        <Stack spacing={2} sx={{ maxWidth: 960 }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Interview transcript
            </Typography>
            <Typography color="text.secondary">
              Upload the interview audio, generate the transcript, then review the text below.
            </Typography>
          </Box>

          {error ? <Alert severity="error">{error}</Alert> : null}
          {success ? <Alert severity="success">{success}</Alert> : null}

          <Paper variant="outlined" sx={{ p: 2 }}>
            <Stack spacing={1.5}>
              <Button variant="outlined" component="label" sx={{ alignSelf: 'flex-start' }}>
                Choose audio file
                <input hidden type="file" accept="audio/*,video/webm" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
              </Button>
              <Typography color={file ? 'text.primary' : 'text.secondary'}>
                {file ? file.name : 'No audio file selected'}
              </Typography>
              <Button variant="contained" disabled={isBusy || (!file && !recordingId)} onClick={generateTranscript} sx={{ alignSelf: 'flex-start' }}>
                {isBusy ? 'Generating transcript…' : 'Generate transcript'}
              </Button>
            </Stack>
          </Paper>

          <TranscriptResult transcript={transcript} />
        </Stack>
      </Paper>
    </Box>
  );
}
