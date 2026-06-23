import { useEffect, useState } from 'react';
import { Alert, Box, Button, CircularProgress, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { assignInterviewer, createInterviewSchedulingRequest, getApplication, getOrganizationMembers } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { getApiErrorMessage } from './recruiterUtils.js';

export default function InterviewAssignmentPage() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const [application, setApplication] = useState(null);
  const [interviewers, setInterviewers] = useState([]);
  const [interviewerId, setInterviewerId] = useState('');
  const [remark, setRemark] = useState('');
  const [assignmentMode, setAssignmentMode] = useState('self_scheduling');
  const [createdInterview, setCreatedInterview] = useState(null);
  const [schedulingRequest, setSchedulingRequest] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    Promise.all([getApplication(applicationId), getOrganizationMembers('')])
      .then(([app, members]) => {
        setApplication(app);
        setInterviewerId(app.assigned_interviewer?.id ?? '');
        setInterviewers(members.filter((member) => member.role === 'interviewer' && member.status === 'active' && member.user_id));
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Unable to load assignment data.')))
      .finally(() => setIsLoading(false));
  }, [applicationId]);

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
      const interview = await assignInterviewer(applicationId, { interviewer_id: Number(interviewerId), remark });
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
    : ' In this backend, only the assigned interviewer can send interview invitations from their portal.';

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
            {!createdInterview && !schedulingRequest ? (
              <Box component="form" onSubmit={assign}>
                <Stack spacing={2}>
                  <TextField label="Scheduling method" select value={assignmentMode} onChange={(e) => setAssignmentMode(e.target.value)}>
                    <MenuItem value="self_scheduling">Self-scheduling request</MenuItem>
                    <MenuItem value="manual_assignment">Manual interviewer assignment</MenuItem>
                  </TextField>
                  <TextField label="Interviewer" select required value={interviewerId} onChange={(e) => setInterviewerId(e.target.value)}>
                    {interviewers.map((member) => <MenuItem key={member.id} value={member.user_id}>{member.full_name} ({member.email})</MenuItem>)}
                  </TextField>
                  <TextField label="Optional remark" multiline minRows={3} value={remark} onChange={(e) => setRemark(e.target.value)} helperText={assignmentMode === 'self_scheduling' ? 'This remark is shown on the scheduling request.' : 'This remark is stored with the assignment workflow.'} />
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
