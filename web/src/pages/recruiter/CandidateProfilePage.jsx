import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Grid, List, ListItem, ListItemText, Paper, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getApplicationStatusHistory, getCandidateProfile, rejectApplication, screenApplication, updateApplicationRemark } from '../../api/client.js';
import RecruiterNav from './RecruiterNav.jsx';
import { applicationName, formatDateTime, getApiErrorMessage, scoreText, titleize } from './recruiterUtils.js';

const EMPTY_EXTRACTION_VALUE = '—';

const formatExtractedValue = (value) => {
  if (value === null || value === undefined || value === '') return EMPTY_EXTRACTION_VALUE;
  if (Array.isArray(value)) {
    const items = value.map(formatExtractedValue).filter((item) => item !== EMPTY_EXTRACTION_VALUE);
    return items.length ? items.join(', ') : EMPTY_EXTRACTION_VALUE;
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value)
      .map(([key, nestedValue]) => [key, formatExtractedValue(nestedValue)])
      .filter(([, formattedValue]) => formattedValue !== EMPTY_EXTRACTION_VALUE);
    return entries.length
      ? entries.map(([key, formattedValue]) => `${titleize(key)}: ${formattedValue}`).join('; ')
      : EMPTY_EXTRACTION_VALUE;
  }
  return String(value);
};

export default function CandidateProfilePage() {
  const { applicationId } = useParams(); const [profile, setProfile] = useState(null); const [history, setHistory] = useState([]); const [remark, setRemark] = useState(''); const [error, setError] = useState(''); const [success, setSuccess] = useState(''); const [isLoading, setIsLoading] = useState(true);
  const load = async () => { setIsLoading(true); try { const [candidate, timeline] = await Promise.all([getCandidateProfile(applicationId), getApplicationStatusHistory(applicationId)]); setProfile(candidate); setRemark(candidate.recruiter_remark ?? ''); setHistory(timeline); } catch (err) { setError(getApiErrorMessage(err, 'Unable to load candidate profile.')); } finally { setIsLoading(false); } };
  useEffect(() => { let active = true; Promise.all([getCandidateProfile(applicationId), getApplicationStatusHistory(applicationId)]).then(([candidate, timeline]) => { if (!active) return; setProfile(candidate); setRemark(candidate.recruiter_remark ?? ''); setHistory(timeline); }).catch((err) => { if (active) setError(getApiErrorMessage(err, 'Unable to load candidate profile.')); }).finally(() => { if (active) setIsLoading(false); }); return () => { active = false; }; }, [applicationId]);
  const runScreen = async () => { try { await screenApplication(applicationId); setSuccess('AI screening completed.'); load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to run AI screening.')); } };
  const saveRemark = async () => { try { await updateApplicationRemark(applicationId, remark); setSuccess('Remark saved.'); } catch (err) { setError(getApiErrorMessage(err, 'Unable to save remark.')); } };
  const reject = async () => { const reason = window.prompt('Reason for rejection?'); if (!reason) return; try { await rejectApplication(applicationId, { reason, remark: reason }); setSuccess('Candidate rejected.'); load(); } catch (err) { setError(getApiErrorMessage(err, 'Unable to reject candidate.')); } };
  const applicant = profile?.applicant_profile;
  return <Box><RecruiterNav /><Paper sx={{ p: 3 }}>{error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}{success ? <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert> : null}{isLoading ? <CircularProgress /> : null}{profile ? <Stack spacing={3}><Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}><Box><Typography variant="h5" sx={{ fontWeight: 700 }}>{applicationName(profile)}</Typography><Typography color="text.secondary">{applicant?.email} • {applicant?.phone_number || 'No phone'}</Typography><Chip label={titleize(profile.status)} sx={{ mt: 1 }} /></Box><Stack direction="row" spacing={1} useFlexGap flexWrap="wrap"><Button onClick={runScreen} variant="contained">Run AI screening</Button><Button component={RouterLink} to={`/recruiter/applications/${applicationId}/assign-interview`} variant="outlined">Assign interviewer</Button><Button component={RouterLink} to={`/recruiter/applications/${applicationId}/hiring-decision`} variant="outlined">Hiring decision</Button><Button color="error" onClick={reject} variant="outlined">Reject</Button></Stack></Stack><Grid container spacing={2}><Grid item xs={12} md={6}><Card><CardContent><Typography variant="h6">Resume and AI extraction</Typography><Typography><strong>Skills:</strong> {(profile.extracted_skills ?? []).join(', ') || '—'}</Typography><Typography><strong>Experience:</strong> {formatExtractedValue(profile.resume_info?.extracted_experience)}</Typography><Typography><strong>Education:</strong> {formatExtractedValue(profile.resume_info?.extracted_education)}</Typography>{profile.resume_info?.resume_url ? <Button href={profile.resume_info.resume_url} target="_blank">Open resume</Button> : null}</CardContent></Card></Grid><Grid item xs={12} md={6}><Card><CardContent><Typography variant="h6">Scores</Typography>{['semantic_score','skill_score','experience_score','education_score','final_score'].map((key) => <Typography key={key}>{titleize(key)}: {scoreText(profile.scores?.[key])}</Typography>)}</CardContent></Card></Grid></Grid><TextField label="Recruiter remark" multiline minRows={3} value={remark} onChange={(e) => setRemark(e.target.value)} /><Button onClick={saveRemark} variant="outlined">Save remark</Button><Box><Typography variant="h6">Stage history</Typography><List>{history.map((item) => <ListItem key={item.id}><ListItemText primary={`${titleize(item.from_stage)} → ${titleize(item.to_stage)}`} secondary={`${item.note || 'No note'} • ${item.changed_by_name || 'System'} • ${formatDateTime(item.changed_at)}`} /></ListItem>)}</List></Box></Stack> : null}</Paper></Box>;
}
