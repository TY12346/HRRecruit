# HRRecruit AI Algorithm Gap Report

## Audit scope

This report audits the current AI-related implementation against `ALGORITHMS.md` and the AI source requirements in `ALGORITHMS_SOURCE.md`.

Audited areas:

1. Resume text extraction from PDF/DOCX
2. Resume preprocessing
3. spaCy-based skill extraction
4. Education extraction
5. Experience extraction
6. Sentence-BERT semantic matching
7. Hybrid scoring formula
8. Candidate ranking API
9. Interview audio transcription service
10. Interview AI summary service
11. Tests for AI behavior
12. Frontend/mobile screens that display AI output

No code was modified as part of this audit. This file is the only implementation artifact produced.

---

## Executive summary

The project already contains a useful early AI-assisted workflow: PDF/DOCX text extraction, dictionary skill extraction, simple education and experience extraction, optional Sentence-BERT matching with a fallback, hybrid scoring, recruiter-triggered screening, candidate ranking, mock transcription, mock interview summary generation, and several backend tests.

However, the current implementation is only partially aligned with `ALGORITHMS.md`. The highest-risk gaps are:

- Skill extraction is not spaCy-based and is not split into the service files recommended by the service-layer rule.
- Resume preprocessing is minimal and not centralized, so semantic matching and extraction do not share a consistent cleaning pipeline.
- Sentence-BERT fallback only catches import failures, not model download/load/runtime failures, so screening can still crash in common FYP demo environments.
- Candidate ranking uses newest application as the tie-breaker, while `ALGORITHMS.md` requires a stable secondary ordering such as `applied_at` ascending.
- Score explanations are nested and omit several required top-level fields/details (`matched_skills`, `missing_skills`, `education_match`, `experience_match`, gaps, human-readable notes).
- Interview transcription and summary services are mock-only and do not support optional real providers controlled by environment variables, although mock fallback exists.
- Some AI API response shapes are likely to break or confuse existing frontend/mobile screens if corrected without a compatibility plan.

---

## Gap details

### 1. Resume text extraction from PDF/DOCX

**Current behavior**

- `backend/apps/ai_services/resume_text_extractor.py` supports `.pdf` and `.docx` local files.
- PDF extraction uses PyMuPDF (`fitz`) and DOCX extraction uses `python-docx` paragraphs plus table cells.
- The extractor validates the extension and file existence.
- The extractor raises `ResumeTextExtractionError` for unsupported types and extraction failures.
- The application screening endpoint catches `ResumeTextExtractionError` and returns a clean serializer validation error.

**Required behavior from `ALGORITHMS.md`**

- Load the resume file for the specified candidate.
- Validate file existence and allowed resume type.
- Extract raw text from PDF or DOCX.
- Clean and normalize extracted text.
- Return and store `parsed_text` / extracted text with structured extraction output.
- Preserve safe fallback/demo reliability where practical.

**Affected files**

- `backend/apps/ai_services/resume_text_extractor.py`
- `backend/apps/ai_services/resume_screening.py`
- `backend/apps/applications/services.py`
- `backend/apps/applications/views.py`
- `backend/apps/applications/models.py`
- `backend/apps/ai_services/tests.py`

**Risk level: medium**

Extraction exists, but there is no graceful fallback for unreadable-but-present supported files. The screening API returns a clean error rather than crashing, but downstream ranking/screening cannot continue with a fallback parsed-text placeholder.

**Recommended fix**

- Keep the existing PyMuPDF and DOCX implementation.
- Add explicit output naming compatibility by mapping stored `extracted_resume_text` to algorithm terminology (`parsed_text`) in the score explanation or API payload.
- Add a safe fallback strategy for unreadable files, such as storing an empty parsed text plus a structured extraction error in `score_explanation`, only if the product wants screening to continue instead of returning a validation error.
- Do not remove the current clean validation errors; they protect API consumers from stack traces.

---

### 2. Resume preprocessing

**Current behavior**

- `resume_text_extractor._clean_text()` strips blank lines and trims each line.
- `skill_extractor.normalize_text()` lowercases and removes most punctuation for skill matching.
- `semantic_matcher.semantic_similarity()` sends raw `resume_text` and raw job comparison text to Sentence-BERT; it only checks for blank strings.
- `resume_screening.py` does not use a shared preprocessing service before semantic matching, education extraction, or experience extraction.

**Required behavior from `ALGORITHMS.md`**

- Clean and normalize extracted resume text before NLP/extraction.
- Clean and preprocess both job text and resume text before semantic matching.
- Keep AI logic inside service files, with suggested service boundaries such as `resume_preprocessor.py`.

**Affected files**

- `backend/apps/ai_services/resume_text_extractor.py`
- `backend/apps/ai_services/skill_extractor.py`
- `backend/apps/ai_services/semantic_matcher.py`
- `backend/apps/ai_services/resume_screening.py`
- Missing/recommended: `backend/apps/ai_services/resume_preprocessor.py`

**Risk level: medium**

Inconsistent preprocessing can produce different scores for equivalent resumes, and raw text may reduce semantic matching quality.

**Recommended fix**

- Add `backend/apps/ai_services/resume_preprocessor.py` with reusable functions for whitespace normalization, lowercasing where appropriate, punctuation handling, token normalization, and optional stopword handling.
- Use preprocessing consistently in text extraction output, skill extraction input, education/experience extraction input, and semantic matching input.
- Keep display text readable by storing raw or lightly cleaned parsed text separately from normalized matching text if needed.

---

### 3. spaCy-based skill extraction

**Current behavior**

- `backend/apps/ai_services/skill_extractor.py` uses a deterministic dictionary and regex alias matching.
- It normalizes aliases such as `js` to the canonical dictionary key `javascript`, `reactjs` to `react`, and `postgres` to `postgresql`.
- It does not import or use spaCy, `PhraseMatcher`, or `Matcher`.
- Canonical skill names are currently lower-case dictionary keys rather than display-normalized names such as `Python`, `React`, or `PostgreSQL`.

**Required behavior from `ALGORITHMS.md`**

- Process cleaned text with spaCy when available.
- Extract skills using spaCy together with practical matching rules.
- Practical implementation may use `en_core_web_sm`, `PhraseMatcher` or `Matcher`, predefined dictionaries, and normalization maps.
- Normalize extracted skill names consistently; example output should use canonical display names such as `Python`, `JavaScript`, `React`, `Node.js`, and `PostgreSQL`.

**Affected files**

- `backend/apps/ai_services/skill_extractor.py`
- `backend/apps/ai_services/resume_screening.py`
- `backend/apps/ai_services/tests.py`
- `backend/requirements.txt`
- Missing/recommended: `backend/apps/ai_services/education_extractor.py`
- Missing/recommended: `backend/apps/ai_services/experience_extractor.py`

**Risk level: high**

This directly diverges from the named algorithm requirement. It may still be acceptable as a fallback, but it is not spaCy-based and it stores lower-case skills that frontend screens display directly.

**Recommended fix**

- Add spaCy as an optional dependency or document setup separately if avoiding a hard install for FYP demo reliability.
- Implement a skill extractor that attempts spaCy + `PhraseMatcher` first and falls back to the current deterministic dictionary method.
- Keep the current dictionary matcher as the fallback path.
- Introduce a canonical display-name map while preserving lower-case matching keys internally if needed.
- Add tests that patch spaCy unavailable and confirm deterministic fallback behavior remains.

---

### 4. Education extraction

**Current behavior**

- Education extraction lives inside `backend/apps/ai_services/resume_screening.py`.
- It detects only the highest broad education level using substring aliases (`secondary`, `diploma`, `associate`, `bachelor`, `master`, `doctorate`).
- It returns `{'level': <level-or-None>}`.
- It does not extract education keywords/details such as field of study (`Computer Science`, `Software Engineering`, `Information Technology`) or matched/missing/gap details.

**Required behavior from `ALGORITHMS.md`**

- Extract education information using keyword and rule-based matching.
- Look for education keywords including `Bachelor`, `Degree`, `Diploma`, `Master`, `PhD`, `Computer Science`, `Software Engineering`, and `Information Technology`.
- Include extracted education in structured output.
- Candidate scoring should identify `education_match` and `education_gap`.

**Affected files**

- `backend/apps/ai_services/resume_screening.py`
- `backend/apps/applications/models.py`
- `backend/apps/applications/serializers.py`
- `web/src/pages/recruiter/CandidateProfilePage.jsx`
- Missing/recommended: `backend/apps/ai_services/education_extractor.py`

**Risk level: medium**

The broad level score works for simple demos but lacks field-of-study matching and gap explanation. The React candidate profile currently attempts to render the extracted education object directly, which may break rendering once AI screening has populated it.

**Recommended fix**

- Move education logic to `backend/apps/ai_services/education_extractor.py`.
- Return structured fields such as `level`, `level_label`, `fields_of_study`, `matched_keywords`, and `raw_mentions`.
- Update `score_explanation` with `education_match` and `education_gap`.
- Update frontend rendering to display structured education values safely rather than rendering an object directly.

---

### 5. Experience extraction

**Current behavior**

- Experience extraction lives inside `backend/apps/ai_services/resume_screening.py`.
- It detects only explicit numeric years with a regex like `2 years` or `5+ yrs` and returns the maximum value as `{'years': 5.0}`.
- It does not detect role phrases such as `software engineer at ABC Company`, `internship`, or `worked as developer`.
- It does not compute/store `experience_match` or `experience_gap` in the explanation.

**Required behavior from `ALGORITHMS.md`**

- Extract experience information using regex and rule-based matching.
- Detect patterns such as `2 years experience`, `3+ years`, `software engineer at ABC Company`, `internship`, and `worked as developer`.
- Candidate scoring should identify `experience_match` and `experience_gap`.

**Affected files**

- `backend/apps/ai_services/resume_screening.py`
- `backend/apps/applications/models.py`
- `backend/apps/applications/serializers.py`
- `web/src/pages/recruiter/CandidateProfilePage.jsx`
- Missing/recommended: `backend/apps/ai_services/experience_extractor.py`

**Risk level: medium**

Experience scoring may be inaccurate for resumes that describe roles without numeric years. The React candidate profile currently attempts to render the extracted experience object directly, which may break rendering once populated.

**Recommended fix**

- Move experience logic to `backend/apps/ai_services/experience_extractor.py`.
- Preserve numeric years extraction but add role/company/internship pattern extraction.
- Return structured fields such as `years`, `roles`, `companies`, `internships`, `matched_phrases`, and `raw_mentions`.
- Update scoring explanation with `experience_match` and `experience_gap`.
- Update frontend rendering to safely format structured experience.

---

### 6. Sentence-BERT semantic matching

**Current behavior**

- `backend/apps/ai_services/semantic_matcher.py` defines `DEFAULT_MODEL_NAME = 'all-MiniLM-L6-v2'`.
- `_get_model()` is cached with `lru_cache(maxsize=1)`, so model loading is not repeated after success.
- If `sentence-transformers` is missing, `semantic_similarity()` returns a configurable fallback score, defaulting to `50.0`.
- Blank resume or job text returns `0.0`.
- It does not catch model download failures, local model load failures, encoding failures, tensor/runtime errors, or offline failures after import succeeds.
- It does not preprocess the resume and job text consistently before embedding.
- `sentence-transformers` is not listed in `backend/requirements.txt`, making the fallback the default in normal installs.

**Required behavior from `ALGORITHMS.md`**

- Use Sentence-BERT `all-MiniLM-L6-v2` when available.
- Generate embeddings for preprocessed job and resume text.
- Compute cosine similarity and normalize to a 0-100 scale.
- Avoid reloading the model unnecessarily.
- Do not use OpenAI for semantic matching.
- If dependency/model/download/local loading fails, use a safe deterministic fallback instead of crashing.

**Affected files**

- `backend/apps/ai_services/semantic_matcher.py`
- `backend/apps/ai_services/resume_screening.py`
- `backend/apps/ai_services/tests.py`
- `backend/requirements.txt`

**Risk level: high**

If `sentence-transformers` is installed but the model cannot download or encode, recruiter-triggered screening can fail. This is a likely FYP demo/runtime problem in offline or restricted environments.

**Recommended fix**

- Catch broader expected exceptions around model load and embedding generation.
- Replace the constant mock score fallback with a deterministic local token-overlap/Jaccard fallback where possible.
- Use shared preprocessing before embedding and fallback scoring.
- Optionally add an environment variable to disable real Sentence-BERT in development.
- Keep `_get_model()` cached.

---

### 7. Hybrid scoring formula

**Current behavior**

- `backend/apps/ai_services/scoring.py` uses the required weights exactly: semantic `0.4`, skill `0.3`, experience `0.2`, education `0.1`.
- It validates component scores are numeric and between 0 and 100.
- `backend/apps/ai_services/resume_screening.py` computes component scores and final score.
- The final score and explanation are stored on `JobApplication`.
- Application status is set to `screened_qualified` or `rejected` based on `SCREENING_THRESHOLD = 60.0`; underqualified applicants are auto-rejected while qualified applicants remain available for recruiter processing.
- `score_explanation` uses nested keys (`semantic`, `skills`, `experience`, `education`) rather than the example structure in `ALGORITHMS.md`.
- The explanation lacks top-level `semantic_score`, `skill_score`, `experience_score`, `education_score`, `final_score`, `matched_skills`, `missing_skills`, `education_match`, `experience_match`, `education_gap`, `experience_gap`, and human-readable `notes`.
- Skill score ignores `JobRequirement.weight_score`; all required skills are weighted equally.

**Required behavior from `ALGORITHMS.md`**

- Calculate final score exactly as `0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score`.
- All scores must use a 0-100 scale.
- Skill score should compare candidate extracted skills with job requirements and any requirement weights.
- Store `final_score` and `score_explanation` JSON including formula, component scores, matched/missing skills, education match details, experience match details, and notes.
- AI screening should auto-reject underqualified applicants while keeping qualified applicants available for recruiter decision-making.

**Affected files**

- `backend/apps/ai_services/scoring.py`
- `backend/apps/ai_services/resume_screening.py`
- `backend/apps/applications/models.py`
- `backend/apps/applications/services.py`
- `backend/apps/applications/serializers.py`
- `backend/apps/ai_services/tests.py`
- `backend/apps/applications/tests.py`

**Risk level: medium**

The formula itself is correct, but the explanation shape and requirement weighting are incomplete. Changing the explanation shape could break any frontend or tests that expect the current nested structure.

**Recommended fix**

- Keep existing nested fields for backward compatibility initially.
- Add required top-level explanation fields alongside the current nested structure.
- Add `education_match`, `education_gap`, `experience_match`, `experience_gap`, and `notes`.
- Incorporate `JobRequirement.weight_score` into skill scoring where skill requirements can be mapped to extracted skills.
- Add tests for weighted skill scoring and explanation keys.

---

### 8. Candidate ranking API

**Current behavior**

- `RankedCandidatesAPIView` is exposed as `GET /jobs/<job_id>/ranked-candidates/`.
- It is recruiter-only and organization/job-owner isolated through `recruiter_job_or_404()`.
- It returns full `JobApplicationSerializer` objects.
- Ordering is `final_score` descending with nulls last, then `-applied_at` (newest application first).
- The React page text explicitly says candidates are sorted by final AI score, then newest application.

**Required behavior from `ALGORITHMS.md`**

- Rank candidates by `final_score` descending.
- If scores are equal, use a stable secondary ordering such as `applied_at` ascending.

**Affected files**

- `backend/apps/applications/views.py`
- `backend/apps/jobs/urls.py`
- `web/src/pages/recruiter/CandidateRankingPage.jsx`
- `web/src/api/client.js`
- `backend/apps/applications/tests.py`

**Risk level: medium**

The primary order is correct, but the tie-breaker contradicts `ALGORITHMS.md`. Changing it will alter visible candidate order and will conflict with the current frontend copy and likely existing tests.

**Recommended fix**

- Change backend ordering to `F('final_score').desc(nulls_last=True), 'applied_at'`.
- Update React copy from “newest application” to “earliest application” or “application time”.
- Update tests that assert ranking order.
- Consider returning `rank` explicitly if frontend ranking display should remain stable across pagination/filtering later.

---

### 9. Interview audio transcription service

**Current behavior**

- Audio upload validates extension, content type, size, and interviewer assignment.
- `backend/apps/ai_services/interview_evaluation.py` provides `transcribe_interview_recording()` as a deterministic mock only.
- `InterviewRecordingTranscribeAPIView` saves the mock transcript to `InterviewTranscript`.
- There is no optional real Whisper/ASR path.
- There are no environment variables such as `USE_REAL_TRANSCRIPTION`, `OPENAI_API_KEY`, or `TRANSCRIPTION_MODEL` wired into the service.
- The mock transcript text is `This is a mock transcript for FYP development.`, which is close to but not exactly the example text in `ALGORITHMS.md`.

**Required behavior from `ALGORITHMS.md`**

- Load and validate interview audio.
- Optionally preprocess audio.
- If real transcription is enabled and available, use Whisper or another ASR service.
- If real transcription is disabled or unavailable, use mock transcription.
- Post-process and save the cleaned transcript.
- Preserve mock fallback so FYP demos do not fail when keys/models/internet are unavailable.

**Affected files**

- `backend/apps/ai_services/interview_evaluation.py`
- `backend/apps/evaluations/views.py`
- `backend/apps/evaluations/models.py`
- `backend/apps/evaluations/serializers.py`
- `backend/apps/interviews/tests.py`
- Recommended split: `backend/apps/ai_services/transcription_service.py`

**Risk level: medium**

Mock fallback supports current demos, but the service does not meet the optional real-provider requirement. Adding real transcription without careful fallbacks could introduce external API failures into tests and demos.

**Recommended fix**

- Split transcription into `backend/apps/ai_services/transcription_service.py`.
- Add env-controlled optional real transcription with default `USE_REAL_TRANSCRIPTION=False`.
- Keep mock transcript as the default and fallback path.
- Save provider/fallback metadata in `transcript_json`.
- Tests must mock any real provider and assert fallback behavior when unavailable.

---

### 10. Interview AI summary service

**Current behavior**

- `backend/apps/ai_services/interview_evaluation.py` provides `generate_interview_summary()` as a deterministic mock only.
- The summary includes the required fields: `strengths`, `weaknesses`, `communication_score`, `overall_impression`, and `editable_summary_text`.
- The summary is saved in `InterviewAISummary` and interviewers can patch it before evaluation submission.
- There is no optional real language model path.
- There are no environment variables such as `USE_REAL_SUMMARY`, `OPENAI_API_KEY`, or `SUMMARY_MODEL` wired into the service.
- `communication_score` is stored and validated on a 0-10 scale, while the algorithm example uses `75`; `ALGORITHMS.md` does not explicitly state the summary score scale, but its example implies a 0-100 score.

**Required behavior from `ALGORITHMS.md`**

- Clean/preprocess transcript text.
- Construct a structured prompt when real summary generation is enabled.
- If real summary generation is enabled and available, call the configured language model.
- If disabled/unavailable, use mock structured summary.
- Validate that all required fields exist.
- Save the structured summary and editable text.
- Allow interviewer edits before final submission.

**Affected files**

- `backend/apps/ai_services/interview_evaluation.py`
- `backend/apps/evaluations/models.py`
- `backend/apps/evaluations/serializers.py`
- `backend/apps/evaluations/views.py`
- `web/src/pages/interviewer/TranscriptSummaryPage.jsx`
- `backend/apps/interviews/tests.py`
- Recommended split: `backend/apps/ai_services/summary_service.py`

**Risk level: medium**

The mock summary flow is functional, but optional real summary generation is absent. The `communication_score` scale mismatch may break UI/backend expectations if changed without migration and validation updates.

**Recommended fix**

- Split summary generation into `backend/apps/ai_services/summary_service.py`.
- Add env-controlled optional real summary generation with default `USE_REAL_SUMMARY=False`.
- Keep deterministic mock summary fallback.
- Decide and document the `communication_score` scale before changing it. If aligning to 0-100, update model validation, frontend labels, tests, and any evaluation reports together.
- Add field validation in the service so malformed real-provider output is converted to fallback-safe structured output.

---

### 11. Tests for AI behavior

**Current behavior**

- `backend/apps/ai_services/tests.py` covers PDF extraction, DOCX extraction, unsupported file type, missing file, skill extraction aliases, semantic fallback on missing dependency, model embedding path, blank semantic input, score validation, final formula, education extraction, experience extraction, skill score, experience score, and education score.
- `backend/apps/applications/tests.py` covers recruiter screening persistence/status behavior and some score explanation output.
- `backend/apps/interviews/tests.py` covers assigned interviewer upload, mock transcription, mock summary generation, summary editing, file type validation, and file size validation.
- There are no tests for spaCy/PhraseMatcher behavior, shared preprocessing, deterministic semantic fallback quality, model load/runtime failure after import, weighted skill scoring, education/experience gap fields, required top-level score explanation fields, ranking tie-breaker ascending, or frontend rendering.

**Required behavior from `ALGORITHMS.md`**

- AI services should be independently testable.
- Add tests for important AI business flows including resume text extraction, skill extraction, skill normalization, education extraction, experience extraction, semantic score normalization, hybrid scoring formula, ranking order, mock transcription, mock summary, and summary editing.

**Affected files**

- `backend/apps/ai_services/tests.py`
- `backend/apps/applications/tests.py`
- `backend/apps/applications/tests_business_flow.py`
- `backend/apps/interviews/tests.py`
- Potential future frontend test files if added under `web/src`
- Potential future mobile widget tests under `mobile/test`

**Risk level: medium**

The current backend tests cover many basics, but gaps allow algorithm regressions in the areas most likely to change next.

**Recommended fix**

- Add tests for every service introduced in the safe implementation order below.
- Add ranking tie-breaker tests before changing ordering.
- Add tests for semantic fallback when `_get_model()` raises a generic exception and when `encode()` fails.
- Add tests for score explanation required keys.
- Consider lightweight frontend rendering tests or manual verification for screens that display structured AI output.

---

### 12. Frontend/mobile screens that display AI output

**Current behavior**

- Web recruiter candidate ranking displays semantic, skill, experience, education, and final scores from the ranked candidates API.
- Web recruiter applications displays final score and has an AI screening action.
- Web recruiter candidate profile displays extracted skills and scores, and attempts to display extracted experience and education from `resume_info`.
- Web recruiter hiring decision displays final AI score as supporting information.
- Web interviewer transcript/summary page can generate mock transcripts and mock AI summaries, displays transcript text, displays editable summary fields, and saves edits.
- Mobile applicant `JobApplication` model has `finalScore`, and application detail displays an `AI score` chip if it is present.
- Backend serializer removes AI fields from applicant responses, so the mobile final score is normally `null`; this is consistent with hiding internal AI screening details from applicants but makes the mobile AI score display effectively inactive.

**Required behavior from `ALGORITHMS.md`**

- AI should support recruiter/interviewer/HR head decision-making and must not make final decisions.
- AI output should be exposed/stored where useful for recruiter/interviewer workflows.
- Interview summary must be editable before final submission.

**Affected files**

- `web/src/pages/recruiter/CandidateRankingPage.jsx`
- `web/src/pages/recruiter/ApplicationsPage.jsx`
- `web/src/pages/recruiter/CandidateProfilePage.jsx`
- `web/src/pages/recruiter/HiringDecisionPage.jsx`
- `web/src/pages/interviewer/TranscriptSummaryPage.jsx`
- `web/src/api/client.js`
- `mobile/lib/models/job_application.dart`
- `mobile/lib/screens/applicant/application_detail_screen.dart`
- `backend/apps/applications/serializers.py`

**Risk level: high**

The current candidate profile screen can break when React tries to render structured experience/education objects directly. Changing API shapes to align with `ALGORITHMS.md` could also break existing web screens if not done additively. Mobile has a dormant AI score field because applicant API responses intentionally strip scores.

**Recommended fix**

- Fix web candidate profile rendering to format structured objects safely before changing backend structures.
- Preserve existing API fields and add new algorithm-compliant fields additively.
- Decide whether applicants should ever see AI scores. If not, remove/hide the mobile AI score chip or leave it harmlessly inactive; if yes, update the backend privacy policy intentionally.
- Update candidate ranking page copy when the tie-breaker changes.
- Add manual testing steps for recruiter ranking, candidate profile, screening, interviewer transcript/summary, and mobile application detail.

---

## Existing API/frontend compatibility risks

The following changes may break existing APIs or frontend/mobile screens if implemented without compatibility precautions:

1. **Ranking tie-breaker change**
   - Current API orders equal scores by `-applied_at`; `ALGORITHMS.md` recommends `applied_at` ascending.
   - Web copy currently says “then newest application”.
   - Safe approach: update backend tests and web copy in the same change.

2. **Score explanation shape**
   - Current explanation is nested under `semantic`, `skills`, `experience`, and `education`.
   - Algorithm example uses top-level component scores and match fields.
   - Existing tests inspect nested fields such as `score_explanation['skills']['matched']`.
   - Safe approach: add top-level fields while preserving nested fields for at least one iteration.

3. **Skill canonical display names**
   - Current API returns lower-case skill keys.
   - Algorithm examples use display names (`Python`, `React`, `PostgreSQL`).
   - Existing tests expect lower-case output.
   - Safe approach: keep lower-case `extracted_skills` initially and add `extracted_skill_labels` or migrate tests/frontend together.

4. **Experience and education object rendering**
   - Current web candidate profile renders `profile.resume_info?.extracted_experience` and `profile.resume_info?.extracted_education` directly.
   - These are JSON objects after screening and can cause React runtime rendering errors.
   - Safe approach: update web formatting before adding richer backend objects.

5. **Communication score scale**
   - Current interview summary validates `communication_score` from 0 to 10.
   - Algorithm example uses `75`, implying a possible 0-100 scale.
   - Safe approach: explicitly decide the scale and migrate backend validation/UI labels/tests together if changing.

6. **Optional real transcription/summary providers**
   - Adding real providers can introduce external failures and slow tests.
   - Safe approach: default real providers off, preserve mock fallback, and mock real-provider tests.

7. **Applicant/mobile AI visibility**
   - Mobile parses/displays `final_score`, but backend removes AI fields for applicants.
   - Safe approach: keep applicant AI details hidden unless explicitly approved, and adjust mobile UI to avoid implying a score will appear.

---

## Recommended safe implementation order

1. **Stabilize frontend rendering before backend payload expansion**
   - Safely format extracted experience/education in the recruiter candidate profile.
   - Update ranking page copy to avoid committing to the wrong tie-breaker.

2. **Add shared resume/job preprocessing service**
   - Create `resume_preprocessor.py` and use it in semantic matching and extraction.
   - Add tests for preprocessing behavior.

3. **Harden semantic matching fallback**
   - Catch model load/download/encode/runtime failures.
   - Add deterministic token-overlap/Jaccard fallback.
   - Add tests for fallback and score normalization.

4. **Split extraction services without changing API output shape**
   - Add `education_extractor.py` and `experience_extractor.py`.
   - Move logic out of `resume_screening.py` while preserving returned JSON shape initially.
   - Add tests for field-of-study, role/company, internship, and years extraction.

5. **Add spaCy-capable skill extraction with fallback**
   - Add optional spaCy/PhraseMatcher path.
   - Keep current dictionary fallback.
   - Preserve existing API fields initially, or add display labels additively.

6. **Expand score explanation additively**
   - Add required top-level formula/component/match/gap/notes fields.
   - Keep current nested fields for compatibility.
   - Add tests for required explanation keys.

7. **Fix candidate ranking tie-breaker**
   - Change equal-score ordering to `applied_at` ascending.
   - Update web copy and tests together.

8. **Introduce transcription and summary service files**
   - Split `interview_evaluation.py` into `transcription_service.py` and `summary_service.py` or keep a compatibility wrapper.
   - Add env-controlled optional real providers with mock fallback as default.
   - Add tests for fallback and provider-disabled behavior.

9. **Revisit frontend/mobile AI visibility and UX**
   - Ensure recruiter and interviewer screens display algorithm outputs clearly.
   - Decide whether mobile applicants should see any AI output; update UI/backend intentionally.

10. **Create/update `AI_ALGORITHM_VALIDATION_REPORT.md` after implementation**
    - Map algorithms to implemented files, endpoints, tests, limitations, fallback behavior, and future enhancements.

---

## Recommended next prompt to run

```text
Read AGENTS.md, FYP_REQUIREMENTS_SUMMARY.md, ALGORITHMS_SOURCE.md, ALGORITHMS.md, and AI_ALGORITHM_GAP_REPORT.md first.

Then implement only the first safe step from the gap report:
1. Fix the recruiter candidate profile frontend so extracted experience and education JSON objects render safely.
2. Update candidate ranking page copy so it does not say equal scores use newest applications.
3. Do not change backend API behavior yet.
4. Add or update tests/checks where practical.

After implementation, list changed files, exact test commands, manual testing steps, and any API compatibility notes.
```
