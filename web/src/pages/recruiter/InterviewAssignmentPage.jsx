import { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { assignInterviewer, createInterviewSchedulingRequest, getApplication, getGoogleCalendarConnectUrl, getGoogleCalendarStatus, getOrganizationMembers } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';
import { buildApplicationTemplateContext, getCommunicationTemplates, renderCommunicationTemplate } from './communicationTemplates.js';

function getGoogleCalendarSetupSteps(calendarStatus) {
  const steps = [];
  if (!calendarStatus?.enabled) {
    steps.push('Set GOOGLE_CALENDAR_ENABLED=true in backend/.env and restart Django.');
  }
  if (!calendarStatus?.client_configured) {
    steps.push('Create a Google Cloud OAuth web client, then set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET in backend/.env.');
  }
  if (!calendarStatus?.redirect_uri_configured) {
    steps.push('Set GOOGLE_CALENDAR_REDIRECT_URI to the same callback URL registered in Google Cloud, for example http://localhost:5173/recruiter/calendar/google/callback.');
  }
  if (!calendarStatus?.dependencies_installed) {
    steps.push('Install the backend Google packages from backend/requirements.txt, then restart Django.');
  }
  return steps;
}

export default function InterviewAssignmentPage() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const [application, setApplication] = useState(null);
  const [interviewers, setInterviewers] = useState([]);
  const [interviewerId, setInterviewerId] = useState('');
  const [remark, setRemark] = useState('');
  const [templateId, setTemplateId] = useState('self_schedule_standard');
  const [assignmentMode, setAssignmentMode] = useState('self_scheduling');
  const [createdInterview, setCreatedInterview] = useState(null);
  const [schedulingRequest, setSchedulingRequest] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [calendarStatus, setCalendarStatus] = useState(null);
  const [isConnectingCalendar, setIsConnectingCalendar] = useState(false);

  useEffect(() => {
    Promise.all([getApplication(applicationId), getOrganizationMembers(''), getGoogleCalendarStatus().catch(() => null)])
      .then(([app, members, googleStatus]) => {
        setApplication(app);
        setRemark(renderCommunicationTemplate(getCommunicationTemplates('interview_self_scheduling')[0], buildApplicationTemplateContext(app)));
        setInterviewerId(app.assigned_interviewer?.id ?? '');
        setCalendarStatus(googleStatus);
        setInterviewers(members.filter((member) => member.role === 'interviewer' && member.status === 'active' && member.user_id));
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load assignment data.')))
      .finally(() => setIsLoading(false));
  }, [applicationId]);

  const templateType = assignmentMode === 'self_scheduling' ? 'interview_self_scheduling' : 'manual_interview_assignment';
  const templates = getCommunicationTemplates(templateType);

  const applyTemplate = (selectedTemplateId) => {
    setTemplateId(selectedTemplateId);
    const selectedTemplate = templates.find((template) => template.id === selectedTemplateId);
    setRemark(renderCommunicationTemplate(selectedTemplate, buildApplicationTemplateContext(application ?? {})));
  };



  const connectGoogleCalendar = async () => {
    setError('');
    setIsConnectingCalendar(true);
    try {
      const callbackUrl = `${window.location.origin}/recruiter/calendar/google/callback`;
      const result = await getGoogleCalendarConnectUrl(callbackUrl);
      window.location.assign(result.authorization_url);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to start Google Calendar connection.'));
    } finally {
      setIsConnectingCalendar(false);
    }
  };

  const assign = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setIsSaving(true);
    try {
      if (assignmentMode === 'self_scheduling') {
        const request = await createInterviewSchedulingRequest(applicationId, { interviewer_id: Number(interviewerId), remark });
        setSchedulingRequest(request);
        setSuccess('Self-scheduling request created. The applicant can now choose from the interviewer availability slots.');
        return;
      }
      const interview = await assignInterviewer(applicationId, { interviewer_id: Number(interviewerId), note: remark });
      setCreatedInterview(interview);
      setSuccess('Interviewer assigned successfully. The interviewer can now continue from their portal.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to assign interviewer.'));
    } finally {
      setIsSaving(false);
    }
  };

  const nextStepMessage = schedulingRequest
    ? `Scheduling request #${schedulingRequest.id} has been created. The interview will be created after the applicant chooses a slot.`
    : `Interview record ${createdInterview ? `#${createdInterview.id}` : 'will be created after assignment'}.`;

  const nextStepHelp = schedulingRequest
    ? ''
    : ' The applicant should use the mobile Schedule interviews page to choose a slot from the interviewer availability.';

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Assign interviewer</Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        {isLoading ? <CircularProgress /> : (
          <Stack spacing={3}>
            <Typography><strong>Candidate:</strong> {application?.applicant?.full_name} for {application?.job_title}</Typography>

            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack spacing={1}>
                <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={1}>
                  <Box>
                    <Typography variant="h6">Calendar sync realism</Typography>
                    <Typography color="text.secondary">Connect a recruiter Google Calendar so booked applicant slots create real calendar events. If it is not connected, HRRecruit still provides a safe fallback calendar link.</Typography>
                  </Box>
                  <Chip
                    color={calendarStatus?.connected ? 'success' : calendarStatus?.oauth_ready ? 'warning' : 'default'}
                    label={calendarStatus?.connected ? 'Google connected' : calendarStatus?.oauth_ready ? 'Ready to connect' : 'Fallback mode'}
                  />
                </Stack>
                <Typography variant="body2" color="text.secondary">
                  Current mode: {calendarStatus?.connected ? `Real Google Calendar sync${calendarStatus.connected_email ? ` (${calendarStatus.connected_email})` : ''}` : calendarStatus?.fallback_mode === 'google_template_link' ? 'Google template link fallback' : 'Local placeholder fallback'}.
                </Typography>
                {!calendarStatus?.connected ? (
                  <Button variant="outlined" onClick={connectGoogleCalendar} disabled={isConnectingCalendar || !calendarStatus?.oauth_ready}>
                    {isConnectingCalendar ? 'Opening Google…' : 'Connect Google Calendar'}
                  </Button>
                ) : null}
                {!calendarStatus?.oauth_ready && !calendarStatus?.connected ? (
                  <Alert severity="info">
                    <Typography sx={{ fontWeight: 700 }}>To enable the Connect Google Calendar button:</Typography>
                    <Box component="ol" sx={{ m: 0, mt: 1, pl: 3 }}>
                      {getGoogleCalendarSetupSteps(calendarStatus).map((step) => (
                        <Box component="li" key={step}>{step}</Box>
                      ))}
                    </Box>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      After setup, reload this page. The mode should change to Ready to connect, then click Connect Google Calendar and approve access with the recruiter Google account.
                    </Typography>
                  </Alert>
                ) : null}
              </Stack>
            </Paper>

            {!createdInterview && !schedulingRequest ? (
              <Box component="form" onSubmit={assign}>
                <Stack spacing={2}>
                  <TextField label="Scheduling method" select value={assignmentMode} onChange={(e) => { const nextMode = e.target.value; setAssignmentMode(nextMode); const nextTemplates = getCommunicationTemplates(nextMode === 'self_scheduling' ? 'interview_self_scheduling' : 'manual_interview_assignment'); if (nextTemplates[0]) { setTemplateId(nextTemplates[0].id); setRemark(renderCommunicationTemplate(nextTemplates[0], buildApplicationTemplateContext(application ?? {}))); } }}>
                    <MenuItem value="self_scheduling">Self-scheduling request</MenuItem>
                    <MenuItem value="manual_assignment">Manual interviewer assignment</MenuItem>
                  </TextField>
                  <TextField label="Interviewer" select required value={interviewerId} onChange={(e) => setInterviewerId(e.target.value)}>
                    {interviewers.map((member) => <MenuItem key={member.id} value={member.user_id}>{member.full_name} ({member.email})</MenuItem>)}
                  </TextField>
                  <TextField label="Candidate communication template" select value={templateId} onChange={(e) => applyTemplate(e.target.value)} helperText="Choose a reusable message style, then edit the text before sending.">{templates.map((template) => <MenuItem key={template.id} value={template.id}>{template.label} — {template.tone}</MenuItem>)}</TextField>
                  <TextField label={assignmentMode === 'self_scheduling' ? 'Candidate scheduling message' : 'Interviewer briefing note'} multiline minRows={3} value={remark} onChange={(e) => setRemark(e.target.value)} helperText={assignmentMode === 'self_scheduling' ? 'This remark is shown on the scheduling request.' : 'This remark is stored with the assignment workflow.'} />
                  <Button type="submit" variant="contained" disabled={isSaving}>{isSaving ? 'Saving…' : assignmentMode === 'self_scheduling' ? 'Create self-scheduling request' : 'Assign interviewer'}</Button>
                </Stack>
              </Box>
            ) : null}
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6">Next step</Typography>
              <Typography color="text.secondary">
                {nextStepMessage}
                {nextStepHelp}
              </Typography>
              <Button disabled={!createdInterview && !schedulingRequest} onClick={() => navigate('/recruiter/interviews')} sx={{ mt: 2 }} variant="outlined">View interviews</Button>
            </Paper>
          </Stack>
        )}
      </Paper>
    </Box>
  );
}
