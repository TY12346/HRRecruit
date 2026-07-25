import { useEffect, useState } from 'react';
import { Autocomplete, Box, Button, Chip, CircularProgress, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import Alert from '../../components/TimedAlert.jsx';
import { useNavigate, useParams } from 'react-router-dom';
import { createInterviewSchedulingRequest, getApplication, getGoogleCalendarConnectUrl, getGoogleCalendarStatus, getInterviewSchedulingRequests, getOrganizationMembers } from '../../api/client.js';
import ApplicantJobSummary from '../../components/ApplicantJobSummary.jsx';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';
import { buildApplicationTemplateContext, getCommunicationTemplates, renderCommunicationTemplate } from './communicationTemplates.js';

export default function InterviewAssignmentPage() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const [application, setApplication] = useState(null);
  const [interviewers, setInterviewers] = useState([]);
  const [interviewerIds, setInterviewerIds] = useState([]);
  const [remark, setRemark] = useState('');
  const [templateId, setTemplateId] = useState('self_schedule_standard');
  const [schedulingRequest, setSchedulingRequest] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [calendarStatus, setCalendarStatus] = useState(null);
  const [isConnectingCalendar, setIsConnectingCalendar] = useState(false);

  useEffect(() => {
    Promise.all([
      getApplication(applicationId),
      getOrganizationMembers(''),
      getGoogleCalendarStatus().catch(() => null),
      getInterviewSchedulingRequests().catch(() => []),
    ])
      .then(([app, members, googleStatus, schedulingRequests]) => {
        setApplication(app);
        setRemark(renderCommunicationTemplate(getCommunicationTemplates('interview_self_scheduling')[0], buildApplicationTemplateContext(app)));
        setInterviewerIds(app.assigned_interviewer?.id ? [app.assigned_interviewer.id] : []);
        setCalendarStatus(googleStatus);
        setInterviewers(members.filter((member) => member.role === 'interviewer' && member.status === 'active' && member.user_id));
        const existingRequest = schedulingRequests
          .filter((request) => request.application?.id === Number(applicationId))
          .sort((a, b) => new Date(b.created_at ?? 0) - new Date(a.created_at ?? 0))[0];
        if (existingRequest) {
          setSchedulingRequest(existingRequest);
          setInterviewerIds((existingRequest.panel_interviewers?.length ? existingRequest.panel_interviewers : [existingRequest.interviewer]).filter(Boolean).map((item) => item.id));
        }
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load assignment data.')))
      .finally(() => setIsLoading(false));
  }, [applicationId]);

  const templates = getCommunicationTemplates('interview_self_scheduling');
  const selectedInterviewers = interviewers.filter((member) => interviewerIds.includes(member.user_id));

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
      const request = await createInterviewSchedulingRequest(applicationId, { interviewer_ids: interviewerIds.map(Number), remark });
      setSchedulingRequest(request);
      if (request.has_common_availability) {
        setSuccess('Panel self-scheduling request created. The applicant can now choose from common panel availability slots.');
      } else {
        setError(request.availability_alert);
      }
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to assign interviewer.'));
    } finally {
      setIsSaving(false);
    }
  };

  const nextStepMessage = schedulingRequest
    ? schedulingRequest.has_common_availability
      ? `Interview-scheduling request #${schedulingRequest.id} has been sent. The interview will be created after the applicant chooses a slot.`
      : `Interview-scheduling request #${schedulingRequest.id} is waiting for a common interviewer timeslot. The applicant has not been invited.`
    : 'The applicant should use the mobile Schedule interviews page to choose a common available panel slot.';

  return (
    <Box>
      <RecruiterNav />
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>Assign panel interviewers</Typography>
        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
        {success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}
        {isLoading ? <CircularProgress /> : (
          <Stack spacing={3}>
            <ApplicantJobSummary applicantName={application?.applicant?.full_name} jobTitle={application?.job_title} />

            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack spacing={1}>
                <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={1}>
                  <Box>
                    <Typography variant="h6">Google Calendar API sync</Typography>
                    <Typography color="text.secondary">Connect a recruiter Google Calendar so booked applicant slots create real Calendar API events, invite the applicant and interviewer, and generate Google Meet links when needed.</Typography>
                  </Box>
                  <Chip
                    color={calendarStatus?.connected ? 'success' : calendarStatus?.oauth_ready ? 'warning' : 'default'}
                    label={calendarStatus?.connected ? 'Google Calendar synced' : calendarStatus?.oauth_ready ? 'Ready to sync with Google Calendar' : 'Google Calendar not synced'}
                  />
                </Stack>
                {!calendarStatus?.connected ? (
                  <Button variant="outlined" onClick={connectGoogleCalendar} disabled={isConnectingCalendar || !calendarStatus?.oauth_ready}>
                    {isConnectingCalendar ? 'Opening Google…' : 'Connect Google Calendar'}
                  </Button>
                ) : null}
                {!calendarStatus?.oauth_ready && !calendarStatus?.connected ? (
                  <Alert severity="info">Set GOOGLE_CALENDAR_ENABLED, GOOGLE_CALENDAR_CLIENT_ID, GOOGLE_CALENDAR_CLIENT_SECRET, GOOGLE_CALENDAR_REDIRECT_URI, and install Google API packages to enable real OAuth.</Alert>
                ) : null}
              </Stack>
            </Paper>

            {!schedulingRequest ? (
              <Box component="form" onSubmit={assign}>
                <Stack spacing={2}>
                  <Autocomplete
                    multiple
                    disableCloseOnSelect
                    options={interviewers}
                    value={selectedInterviewers}
                    isOptionEqualToValue={(option, value) => option.user_id === value.user_id}
                    getOptionLabel={(option) => `${option.full_name} (${option.email})`}
                    onChange={(_, selectedMembers) => setInterviewerIds(selectedMembers.map((member) => member.user_id))}
                    renderTags={(selectedMembers, getTagProps) => selectedMembers.map((member, index) => {
                      const { key, ...tagProps } = getTagProps({ index });
                      return <Chip key={key} label={member.full_name} {...tagProps} />;
                    })}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Panel interviewers"
                        required={interviewerIds.length === 0}
                        helperText="Select one or more interviewers. Applicants will only see time slots when every panel interviewer is available."
                      />
                    )}
                  />
                  <TextField label="Applicant scheduling message" multiline minRows={3} value={remark} onChange={(e) => setRemark(e.target.value)} />
                  <Button type="submit" variant="contained" disabled={isSaving || interviewerIds.length === 0}>{isSaving ? 'Saving…' : 'Create self-scheduling request'}</Button>
                </Stack>
              </Box>
            ) : null}
          </Stack>
        )}
      </Paper>
    </Box>
  );
}
