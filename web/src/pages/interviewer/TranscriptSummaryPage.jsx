import { useEffect, useState } from 'react';
import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useLocation, useParams } from 'react-router-dom';
import { generateTranscriptSummary, getInterview, transcribeRecording, uploadInterviewRecording } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { getApiErrorMessage, getStoredRecordingId, setStoredRecordingId, setStoredSummaryId, setStoredTranscriptId } from './interviewerUtils.js';

const speakerSeparationMessages = {
  not_configured: 'Speaker separation is turned off in backend settings. The plain transcript was generated successfully.',
  unavailable: 'Speaker separation is unavailable for this transcript. The plain transcript was generated successfully.',
  failed: 'Speaker separation could not be completed for this transcript. The plain transcript was generated successfully.',
};


function getDisplayRole(role, speakerId) {
  return role || speakerId || 'Unknown speaker';
}

function mergeConsecutiveSpeakerSegments(segments) {
  return segments.reduce((groups, segment) => {
    const text = String(segment.text || '').trim();
    if (!text) return groups;

    const role = getDisplayRole(segment.role, segment.speaker_id);
    const previous = groups[groups.length - 1];
    if (previous?.role === role) {
      previous.text = `${previous.text} ${text}`;
      previous.end_time = segment.end_time ?? previous.end_time;
      return groups;
    }

    groups.push({
      role,
      text,
      speaker_id: segment.speaker_id || 'UNKNOWN',
      start_time: segment.start_time,
      end_time: segment.end_time,
    });
    return groups;
  }, []);
}

function TranscriptResult({ transcript }) {
  if (!transcript) return null;

  const processingStatus = transcript.processing_status || 'COMPLETED';
  const displayTranscript = transcript.speaker_labelled_transcript || transcript.transcript_text || transcript.transcript || '';
  const speakerSegments = Array.isArray(transcript.speaker_segments) ? transcript.speaker_segments : [];
  const mergedSpeakerSegments = mergeConsecutiveSpeakerSegments(speakerSegments);
  const diarizationStatus = transcript.diarization_status || transcript.transcript_json?.diarization_status || 'unavailable';
  const diarizationWarning = transcript.diarization_warning || transcript.transcript_json?.diarization_warning || '';
  const showDiarizationWarningDetail = diarizationWarning && diarizationStatus !== 'not_configured';
  const speakerSeparationMessage = speakerSeparationMessages[diarizationStatus] || 'Speaker separation is not available for this transcript. The plain transcript was generated successfully.';
  const showSpeakerUnavailable = diarizationStatus !== 'completed';
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={1.5}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>Generated transcript</Typography>
        {processingStatus === 'PENDING' || processingStatus === 'PROCESSING' ? <Alert severity="info">Processing real transcription… This page refreshes automatically.</Alert> : null}
        {processingStatus === 'FAILED' ? <Alert severity="error">Real transcription failed: {transcript.processing_error || transcript.transcript_json?.error || 'No error details were returned.'}</Alert> : null}
        {processingStatus === 'LOW_QUALITY' ? <Alert severity="error">Real transcription completed but failed quality checks and cannot be summarized: {transcript.processing_error || 'The returned text is likely unusable.'}</Alert> : null}
        {processingStatus === 'COMPLETED' && showSpeakerUnavailable ? (
          <Alert severity="info">
            <Stack spacing={0.5}>
              <Typography variant="body2">{speakerSeparationMessage}</Typography>
              {showDiarizationWarningDetail ? (
                <Typography variant="body2" color="text.secondary">
                  Detail: {diarizationWarning}
                </Typography>
              ) : null}
            </Stack>
          </Alert>
        ) : null}
        {mergedSpeakerSegments.length ? (
          <Stack spacing={2}>
            {mergedSpeakerSegments.map((segment, index) => (
              <Box key={`${segment.speaker_id || 'speaker'}-${segment.start_time || index}-${index}`}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                  {segment.role}
                </Typography>
                <Typography variant="body1">{segment.text}</Typography>
              </Box>
            ))}
          </Stack>
        ) : (
          <Typography variant="body1" whiteSpace="pre-line">
            {displayTranscript || 'No transcript text returned.'}
          </Typography>
        )}
      </Stack>
    </Paper>
  );
}


function SummaryResult({ summary }) {
  if (!summary) return null;

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={1}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>AI summary</Typography>
        <Typography><strong>Strengths:</strong> {summary.strengths || '—'}</Typography>
        <Typography><strong>Weaknesses:</strong> {summary.weaknesses || '—'}</Typography>
        <Typography><strong>Communication score:</strong> {summary.communication_score ?? '—'}</Typography>
        <Typography><strong>Overall impression:</strong> {summary.overall_impression || '—'}</Typography>
        <Typography whiteSpace="pre-line"><strong>Overall summary:</strong> {summary.editable_summary_text || '—'}</Typography>
      </Stack>
    </Paper>
  );
}

export default function TranscriptSummaryPage() {
  const { interviewId } = useParams();
  const location = useLocation();
  const [recordingId, setRecordingId] = useState(String(location.state?.recordingId ?? getStoredRecordingId(interviewId) ?? ''));
  const [file, setFile] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [isSummaryBusy, setIsSummaryBusy] = useState(false);

  useEffect(() => {
    let isActive = true;
    setError('');
    getInterview(interviewId)
      .then((interview) => {
        if (!isActive) return;
        const storedRecording = interview.latest_recording;
        const storedTranscript = interview.transcript;
        const storedSummary = interview.ai_summary;
        if (storedRecording?.id) {
          setRecordingId(String(storedRecording.id));
          setStoredRecordingId(interviewId, storedRecording.id);
        }
        if (storedTranscript) {
          setTranscript(storedTranscript);
          setStoredTranscriptId(interviewId, storedTranscript.id);
        }
        if (storedSummary) {
          setSummary(storedSummary);
          setStoredSummaryId(interviewId, storedSummary.id);
        }
      })
      .catch((err) => {
        if (isActive) setError(getApiErrorMessage(err, 'Unable to load stored transcript and summary.'));
      });
    return () => { isActive = false; };
  }, [interviewId]);

  useEffect(() => {
    if (!transcript?.id || !['PENDING', 'PROCESSING'].includes(transcript.processing_status)) return undefined;
    const timer = window.setInterval(async () => {
      try {
        const interview = await getInterview(interviewId);
        if (interview.transcript?.id === transcript.id) setTranscript(interview.transcript);
      } catch (_) { /* keep polling; surfaced on next explicit action */ }
    }, 2500);
    return () => window.clearInterval(timer);
  }, [interviewId, transcript?.id, transcript?.processing_status]);

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
      setSummary(null);
      setStoredTranscriptId(interviewId, data.id);
      setSuccess(data.processing_status === 'COMPLETED' ? 'Transcript generated and stored successfully.' : 'Real transcription has been queued.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to generate transcript.'));
    } finally {
      setIsBusy(false);
    }
  };


  const generateSummary = async () => {
    if (!transcript?.id) {
      setError('Generate or load a transcript before generating the AI summary.');
      return;
    }
    setError('');
    setSuccess('');
    setIsSummaryBusy(true);
    try {
      const data = await generateTranscriptSummary(transcript.id);
      setSummary(data);
      setStoredSummaryId(interviewId, data.id);
      setSuccess('AI summary generated and stored successfully.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to generate AI summary.'));
    } finally {
      setIsSummaryBusy(false);
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
              <Typography color={file ? 'text.primary' : recordingId ? 'text.primary' : 'text.secondary'}>
                {file ? file.name : recordingId ? `Stored recording #${recordingId} loaded` : 'No audio file selected'}
              </Typography>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                <Button variant="contained" disabled={isBusy || (!file && !recordingId)} onClick={generateTranscript}>
                  {isBusy ? 'Queueing real transcription…' : transcript ? 'Regenerate transcript' : 'Generate transcript'}
                </Button>
                <Button variant="outlined" disabled={isSummaryBusy || !transcript?.id || transcript.processing_status !== 'COMPLETED'} onClick={generateSummary}>
                  {isSummaryBusy ? 'Generating summary…' : summary ? 'Regenerate AI summary' : 'Generate AI summary'}
                </Button>
              </Stack>
            </Stack>
          </Paper>

          <TranscriptResult transcript={transcript} />
          <SummaryResult summary={summary} />
        </Stack>
      </Paper>
    </Box>
  );
}
