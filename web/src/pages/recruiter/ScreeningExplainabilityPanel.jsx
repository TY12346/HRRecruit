import { Alert, Box, Card, CardContent, Chip, Divider, Grid, Stack, Typography } from '@mui/material';
import { buildScreeningExplainability } from './screeningExplainability.js';

const pct = (value) => value === null || value === undefined ? '—' : `${Number(value).toFixed(2)}%`;
const MATCH_LABELS = {
  direct_phrase_match: 'Direct phrase match',
  lexical_match: 'Lexical match',
  semantic_paraphrase: 'Related meaning detected despite different wording',
  insufficient_evidence: 'Insufficient evidence',
};

export default function ScreeningExplainabilityPanel({ profile, compact = false }) {
  const data = buildScreeningExplainability(profile);
  if (!data.explanation || !Object.keys(data.explanation).length) {
    return <Alert severity="info">No screening result is available. Run AI screening to generate a live explainable analysis.</Alert>;
  }
  const live = data.provenance === 'live_screening';
  return <Stack spacing={2}>
    <Card variant="outlined"><CardContent>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
        <Box><Typography variant="overline">Hybrid screening result</Typography>
          <Typography variant="h4" fontWeight={700}>{pct(data.finalScore)}</Typography>
          <Chip label={data.fit.label} color={data.fit.color} size="small" /></Box>
        <Stack spacing={0.5}>
          <Typography><strong>AI semantic component:</strong> {data.modelVersion}</Typography>
          <Typography><strong>Generated:</strong> {data.generatedAt ? new Date(data.generatedAt).toLocaleString() : 'Not recorded'}</Typography>
          <Typography><strong>Analysis ID:</strong> {data.analysisId || 'Legacy result'}</Typography>
          <Stack direction="row" gap={1} flexWrap="wrap"><Chip color={live ? 'success' : 'warning'} label={live ? 'Live analysis' : data.provenance === 'seeded_demo_fixture' ? 'Seeded demo result' : 'Legacy result'} />
            <Chip label={`${data.reliableEvidenceCount} reliable evidence matches`} /><Chip label={`${data.differentWordingCount} semantic paraphrases`} /></Stack>
        </Stack>
      </Stack>
    </CardContent></Card>
    <Box><Typography variant="h6" gutterBottom>Score-component breakdown</Typography>
      <Grid container spacing={1.5}>{data.scoreComponents.map((component) => <Grid key={component.key} size={{ xs: 12, sm: 6, lg: 3 }}>
        <Card variant="outlined" sx={{ height: '100%' }}><CardContent>
          <Typography fontWeight={700}>{component.label}</Typography><Typography variant="h6">{pct(component.value)}</Typography>
          <Typography variant="body2">Weight: {Number(component.weight * 100).toFixed(0)}% · Contribution: {pct(component.weighted_contribution)}</Typography>
          <Typography variant="body2" color="text.secondary">{component.method}</Typography>
        </CardContent></Card></Grid>)}</Grid>
      <Typography sx={{ mt: 1 }} fontWeight={700}>Weighted contributions = {pct(data.finalScore)} final score</Typography>
    </Box>
    {!compact ? <>
      <Divider /><Box><Typography variant="h6">Sentence-BERT semantic evidence</Typography>
        <Typography color="text.secondary" gutterBottom>{data.semanticAnalysis.algorithm || 'Algorithm metadata unavailable'}</Typography>
        {data.evidencePairs.length ? <Stack spacing={1.5}>{data.evidencePairs.map((pair, index) => <Card variant="outlined" key={`${pair.requirement_type}-${pair.requirement_text}-${pair.rank}-${index}`}><CardContent>
          <Stack direction="row" gap={1} flexWrap="wrap"><Chip size="small" label={pair.requirement_type || 'other'} /><Chip size="small" variant="outlined" label={pair.evidence_section ? `Resume section: ${pair.evidence_section}` : 'No compatible section'} />
            <Chip size="small" color={pair.reliable_evidence ? (pair.match_type === 'semantic_paraphrase' ? 'secondary' : 'success') : 'warning'} label={MATCH_LABELS[pair.match_type] || 'Unclassified'} />
            {pair.semantic_similarity_score !== null && pair.semantic_similarity_score !== undefined ? <Chip size="small" variant="outlined" label={`Semantic similarity ${pct(pair.semantic_similarity_score)}`} /> : null}</Stack>
          <Grid container spacing={2} sx={{ mt: 0.5 }}><Grid size={{ xs: 12, md: 6 }}><Typography variant="caption">JOB REQUIREMENT</Typography><Typography>{pair.requirement_text}</Typography></Grid>
            <Grid size={{ xs: 12, md: 6 }}><Typography variant="caption">RESUME EVIDENCE</Typography><Typography>{pair.resume_evidence}</Typography></Grid></Grid>
          <Typography variant="body2" sx={{ mt: 1 }}><strong>Lexical overlap:</strong> {pct(pair.lexical_overlap_score)}</Typography>
          {pair.shared_terms?.length ? <Typography variant="body2"><strong>Exact shared terms:</strong> {pair.shared_terms.join(', ')}</Typography> : null}
          {!pair.reliable_evidence && pair.suppression_reason ? <Typography variant="body2" color="text.secondary">Suppressed: {pair.suppression_reason.replaceAll('_', ' ')}</Typography> : null}
        </CardContent></Card>)}</Stack> : <Alert severity="warning">Detailed semantic evidence is unavailable for this older screening result. Refresh AI screening to generate a live explainable analysis.</Alert>}
      </Box>
      <Box><Typography variant="h6">Structured rule-based evidence</Typography>
        <Typography><strong>Matched skills:</strong> {data.matchedSkills.join(', ') || 'None recorded'}</Typography><Typography><strong>Missing skills:</strong> {data.missingSkills.join(', ') || 'None recorded'}</Typography>
        <Typography><strong>Experience:</strong> extracted {data.explanation.experience?.extracted_years ?? '—'} years; required {data.explanation.experience?.required_years ?? '—'} years; gap {data.explanation.experience?.gap?.missing_years ?? '—'} years</Typography>
        <Typography><strong>Education:</strong> extracted {data.explanation.education?.extracted_level ?? '—'}; required {data.explanation.education?.required_level ?? '—'}</Typography>
      </Box>
    </> : null}
    <Alert severity="info">This screening result supports recruiter review. Semantic similarity indicates contextual relevance but does not verify that the applicant truly possesses a skill or should be hired.</Alert>
  </Stack>;
}
