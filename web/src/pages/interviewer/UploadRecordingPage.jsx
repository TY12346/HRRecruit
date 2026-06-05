import { useState } from 'react';
import { Alert, Box, Button, Paper, Stack, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { uploadInterviewRecording } from '../../api/client.js';
import InterviewerNav from './InterviewerNav.jsx';
import { getApiErrorMessage, setStoredRecordingId } from './interviewerUtils.js';

export default function UploadRecordingPage() {
  const { interviewId } = useParams(); const navigate = useNavigate(); const [file, setFile] = useState(null); const [recording, setRecording] = useState(null); const [error, setError] = useState(''); const [isUploading, setIsUploading] = useState(false);
  const submit = async (event) => { event.preventDefault(); if (!file) return; setError(''); setIsUploading(true); try { const data = await uploadInterviewRecording(interviewId, file); setRecording(data); setStoredRecordingId(interviewId, data.id); } catch (err) { setError(getApiErrorMessage(err, 'Unable to upload recording.')); } finally { setIsUploading(false); } };
  return <Box><InterviewerNav /><Paper sx={{ p: 3 }}><Typography variant="h5" sx={{ fontWeight: 700 }}>Upload Interview Recording</Typography><Typography color="text.secondary" sx={{ mb: 2 }}>Upload mp3, wav, m4a, ogg, webm, or aac audio up to the backend limit.</Typography>{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{recording ? <Alert severity="success" sx={{ mb: 2 }}>Recording #{recording.id} uploaded successfully.</Alert> : null}<Stack component="form" spacing={2} onSubmit={submit}><Button variant="outlined" component="label">Choose audio file<input hidden type="file" accept="audio/*,video/webm" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></Button><Typography>{file ? file.name : 'No file selected'}</Typography><Stack direction="row" spacing={1}><Button type="submit" variant="contained" disabled={!file || isUploading}>{isUploading ? 'Uploading…' : 'Upload recording'}</Button><Button variant="outlined" disabled={!recording} onClick={() => navigate(`/interviewer/interviews/${interviewId}/transcript-summary`, { state: { recordingId: recording?.id } })}>Generate transcript</Button></Stack></Stack></Paper></Box>;
}
