# AI Algorithm Validation Report

This report validates the current HRRecruit AI-assisted implementation against `ALGORITHMS.md`, with emphasis on deterministic local behavior for FYP demo reliability and tests that avoid real external API calls.

## Validation scope

- Source requirements: `ALGORITHMS.md`, derived from `ALGORITHMS_SOURCE.md`.
- Backend scope: resume extraction, preprocessing, skill/education/experience extraction, semantic matching, hybrid ranking, interview transcription, and interview summary generation.
- Reliability constraint: tests and default demo flows use local/mock behavior only; real OpenAI calls are disabled unless explicitly configured outside tests.

## Regression test coverage summary

| Required coverage item | Test coverage |
| --- | --- |
| PDF resume text extraction | `ResumeTextExtractorTests.test_extract_resume_text_from_pdf` in `backend/apps/ai_services/tests.py` |
| DOCX resume text extraction | `ResumeTextExtractorTests.test_extract_resume_text_from_docx_includes_paragraphs_and_table_cells` in `backend/apps/ai_services/tests.py` |
| Resume/job preprocessing | `ResumePreprocessorTests` in `backend/apps/ai_services/tests.py` and screening endpoint tests in `backend/apps/applications/tests.py` |
| Skill extraction and alias normalization | `SkillExtractorTests` in `backend/apps/ai_services/tests.py` |
| spaCy unavailable fallback | `SkillExtractorTests.test_extract_skills_uses_deterministic_fallback_when_spacy_unavailable` |
| Education extraction | `ResumeScreeningScoreComponentTests` education tests in `backend/apps/ai_services/tests.py` |
| Experience extraction | `ResumeScreeningScoreComponentTests` experience tests in `backend/apps/ai_services/tests.py` |
| Semantic score normalization | `SemanticMatcherTests.test_semantic_similarity_normalizes_model_scores_to_zero_to_one_hundred` |
| Semantic fallback when Sentence-BERT/model fails | `SemanticMatcherTests` dependency/model/encoding/tensor fallback tests |
| Hybrid final score formula | `ScoringTests.test_calculate_final_score_matches_exact_required_formula` |
| Weighted skill scoring | `ResumeScreeningScoreComponentTests.test_skill_score_uses_requirement_weight_scores_when_available` and application endpoint weighted scoring test |
| Required `score_explanation` fields | `test_job_owner_screens_uploaded_resume_and_persists_qualified_breakdown` and `test_score_explanation_contains_nested_required_sections_for_not_qualified_screening` |
| Candidate ranking order | `test_recruiter_views_ranked_candidates_for_own_job_only` and `test_ranked_candidates_use_earliest_application_as_equal_score_tie_breaker_and_nulls_last` |
| `screened_qualified` vs auto-rejected underqualified behavior | Qualified and low-score screening endpoint tests in `backend/apps/applications/tests.py` |
| No automatic rejection by AI | `test_low_score_marks_application_not_qualified_without_rejecting_it` |
| Mock transcription | `test_mock_transcription_is_default_and_saves_metadata` |
| Transcription fallback behavior | Missing API-key and provider-failure transcription fallback tests |
| Transcript saving | `test_transcription_response_is_saved_for_existing_evaluation_flow` |
| Mock AI summary | `test_mock_summary_is_default_and_saves_structured_fields` |
| Summary required fields | `test_summary_response_contains_required_structured_output_fields` |
| Summary edit flow | `test_interviewer_can_edit_generated_summary_before_final_evaluation` |
| External APIs are not called in tests | Transcription and summary disabled tests assert OpenAI helper methods are not called; optional enabled-provider paths patch provider helpers so no network call occurs |

## Algorithm mapping

### 1. Resume text extraction and preprocessing

- **Implemented files**
  - `backend/apps/ai_services/resume_text_extractor.py`
  - `backend/apps/ai_services/resume_preprocessor.py`
  - `backend/apps/ai_services/resume_screening.py`
  - `backend/apps/applications/services.py`
- **Endpoints involved**
  - `POST /api/applications/<application_id>/screen/`
  - `GET /api/applications/<application_id>/candidate-profile/`
- **Tests added/confirmed**
  - PDF extraction, DOCX paragraph/table extraction, unsupported extension, missing file, whitespace cleanup, punctuation cleanup, matching preprocessing, and semantic preprocessing are covered in `backend/apps/ai_services/tests.py`.
  - Screening persistence through the recruiter endpoint is covered in `backend/apps/applications/tests.py`.
- **Current limitations**
  - PDF/DOCX extraction depends on local parser libraries and does not perform OCR for scanned resumes.
  - Extraction quality depends on resume formatting; highly graphical resumes may lose structure.
- **Fallback behavior**
  - Unsupported or missing files return clean validation errors through the screening endpoint.
  - Preprocessing is deterministic and local.
- **Future enhancement**
  - Add optional OCR for scanned PDFs only when explicitly requested.
  - Store extracted resume sections separately for richer recruiter review.
- **Manual test steps**
  1. Log in as a recruiter who owns a job.
  2. Ensure an applicant uploaded a PDF or DOCX resume.
  3. Call `POST /api/applications/<application_id>/screen/`.
  4. Verify `extracted_resume_text`, extracted skills, scores, and `score_explanation` are returned.

### 2. Skill extraction with spaCy/PhraseMatcher and deterministic fallback

- **Implemented files**
  - `backend/apps/ai_services/skill_extractor.py`
  - `backend/apps/ai_services/resume_screening.py`
- **Endpoints involved**
  - `POST /api/applications/<application_id>/screen/`
  - `GET /api/jobs/<job_id>/ranked-candidates/`
  - `GET /api/applications/<application_id>/candidate-profile/`
- **Tests added/confirmed**
  - Alias normalization (`py`, `js`, `reactjs`, `nodejs`, `postgres`) and canonical display labels are covered in `SkillExtractorTests`.
  - spaCy unavailable fallback is covered by patching the spaCy loader to `None`.
  - spaCy/PhraseMatcher behavior is covered with fake local matcher classes.
- **Current limitations**
  - Skill dictionaries are predefined and may miss uncommon or domain-specific skills.
  - spaCy is optional; the default demo path may use deterministic dictionary matching.
- **Fallback behavior**
  - If spaCy/model loading is unavailable, extraction uses local deterministic dictionary/rule matching.
- **Future enhancement**
  - Expand skill dictionaries from FYP sample datasets.
  - Add organization-specific skill aliases and recruiter-maintained skill vocabularies.
- **Manual test steps**
  1. Upload a resume containing aliases such as `py`, `reactjs`, `nodejs`, and `postgres`.
  2. Trigger screening.
  3. Confirm the response stores normalized skills such as `python`, `react`, `node.js`, and `postgresql`.

### 3. Education extraction

- **Implemented files**
  - `backend/apps/ai_services/education_extractor.py`
  - `backend/apps/ai_services/resume_screening.py`
- **Endpoints involved**
  - `POST /api/applications/<application_id>/screen/`
  - `GET /api/applications/<application_id>/candidate-profile/`
- **Tests added/confirmed**
  - Highest education level, preprocessing, supported levels, fields of study, and structured keys are covered in `backend/apps/ai_services/tests.py`.
  - Screening endpoint persistence and `education_match`/`education_gap` fields are covered in `backend/apps/applications/tests.py`.
- **Current limitations**
  - Rule-based matching may not understand all international qualification names.
  - It captures broad levels and known fields rather than full institution history.
- **Fallback behavior**
  - Missing education returns structured empty values and produces an education gap instead of crashing.
- **Future enhancement**
  - Add configurable qualification equivalency mapping for Malaysian and international credentials.
- **Manual test steps**
  1. Configure a job education requirement such as `Bachelor Degree in Computer Science`.
  2. Screen resumes with and without this qualification.
  3. Verify `education_score`, `education_match`, and `education_gap` in `score_explanation`.

### 4. Experience extraction

- **Implemented files**
  - `backend/apps/ai_services/experience_extractor.py`
  - `backend/apps/ai_services/resume_screening.py`
- **Endpoints involved**
  - `POST /api/applications/<application_id>/screen/`
  - `GET /api/applications/<application_id>/candidate-profile/`
- **Tests added/confirmed**
  - Explicit year extraction, regex preprocessing, role/company detection, internship detection, and structured keys are covered in `backend/apps/ai_services/tests.py`.
  - Screening endpoint persistence and `experience_match`/`experience_gap` fields are covered in `backend/apps/applications/tests.py`.
- **Current limitations**
  - Overlapping jobs are not timeline-normalized.
  - Experience seniority is inferred from text patterns, not verified employment history.
- **Fallback behavior**
  - If no years or roles are found, structured zero/empty values are returned and scoring continues.
- **Future enhancement**
  - Add date-range extraction and deduplicate overlapping employment periods.
- **Manual test steps**
  1. Configure a job experience requirement such as `3 years software engineer experience`.
  2. Screen resumes containing `5+ yrs`, `software engineer at ABC Company`, or `internship`.
  3. Verify extracted years, roles, companies, and score explanation gaps.

### 5. Sentence-BERT semantic matching with deterministic fallback

- **Implemented files**
  - `backend/apps/ai_services/semantic_matcher.py`
  - `backend/apps/ai_services/resume_screening.py`
- **Endpoints involved**
  - `POST /api/applications/<application_id>/screen/`
  - `GET /api/jobs/<job_id>/ranked-candidates/`
- **Tests added/confirmed**
  - Model embedding path, 0-100 normalization, blank input, missing dependency fallback, model-load failure fallback, encoding failure fallback, tensor handling fallback, and deterministic token-overlap fallback are covered in `backend/apps/ai_services/tests.py`.
- **Current limitations**
  - When Sentence-BERT is unavailable, fallback is token-overlap/Jaccard style and less semantic than embeddings.
  - No OpenAI semantic matching is used by design.
- **Fallback behavior**
  - Any optional dependency, model download, model loading, encoding, tensor, or runtime failure returns a deterministic local fallback score.
- **Future enhancement**
  - Package a local Sentence-BERT model artifact for offline demos or CI if storage constraints allow.
- **Manual test steps**
  1. Run screening with `sentence-transformers` installed to use the model path.
  2. Run screening without `sentence-transformers` or with model loading unavailable.
  3. Verify screening still completes and returns `semantic_score` on a 0-100 scale.

### 6. Hybrid candidate scoring and ranking

- **Implemented files**
  - `backend/apps/ai_services/scoring.py`
  - `backend/apps/ai_services/resume_screening.py`
  - `backend/apps/applications/services.py`
  - `backend/apps/applications/views.py`
  - `backend/apps/applications/serializers.py`
- **Endpoints involved**
  - `POST /api/applications/<application_id>/screen/`
  - `GET /api/jobs/<job_id>/ranked-candidates/`
  - `GET /api/applications/<application_id>/candidate-profile/`
- **Tests added/confirmed**
  - Exact formula `0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score` is covered in `ScoringTests`.
  - Weighted skill scoring is covered at service level and endpoint level.
  - Candidate ranking order is covered, including null scores last and earliest application as equal-score tie breaker.
  - `screened_qualified` and auto-rejected underqualified behavior is covered through recruiter endpoint tests.
  - Underqualified AI rejection is covered by ensuring low scores become `rejected`, while qualified applicants remain in recruiter review.
- **Current limitations**
  - Requirement weights currently influence skill scoring where configured; other score component weighting is fixed by `ALGORITHMS.md`.
  - Candidate ranking is score-first and does not include fairness/bias audit metrics.
- **Fallback behavior**
  - Missing optional AI dependencies do not block final scoring because extraction and semantic matching have local fallbacks.
- **Future enhancement**
  - Add recruiter-facing explanation UI for every score component and a bias/fairness checklist before decisions.
- **Manual test steps**
  1. Create multiple applications for a job.
  2. Screen each application.
  3. Call `GET /api/jobs/<job_id>/ranked-candidates/`.
  4. Verify descending `final_score`, equal-score tie by earlier `applied_at`, and unscored candidates last.

### 7. Interview transcription

- **Implemented files**
  - `backend/apps/ai_services/transcription_service.py`
  - `backend/apps/evaluations/views.py`
  - `backend/apps/evaluations/models.py`
  - `backend/apps/evaluations/serializers.py`
- **Endpoints involved**
  - `POST /api/interviews/<interview_id>/recordings/`
  - `POST /api/evaluations/recordings/<recording_id>/transcribe/`
- **Tests added/confirmed**
  - Upload/transcribe flow, mock transcription default, missing API-key fallback, provider-failure fallback, transcript saving, and no external API when disabled are covered in `backend/apps/interviews/tests.py`.
- **Current limitations**
  - Default transcript is a deterministic mock transcript for FYP development.
  - Real transcription is optional and not used during tests.
- **Fallback behavior**
  - Real transcription is disabled by default.
  - Missing API key or provider failure returns a mock transcript with fallback metadata and saves it for the evaluation flow.
- **Future enhancement**
  - Add optional local speech-to-text or explicitly configured provider integration after the FYP demo.
- **Manual test steps**
  1. Log in as an assigned interviewer.
  2. Upload an audio file through `POST /api/interviews/<interview_id>/recordings/`.
  3. Call `POST /api/evaluations/recordings/<recording_id>/transcribe/`.
  4. Verify the transcript text, metadata provider, and saved transcript record.

### 8. Interview AI summary and edit flow

- **Implemented files**
  - `backend/apps/ai_services/summary_service.py`
  - `backend/apps/evaluations/views.py`
  - `backend/apps/evaluations/models.py`
  - `backend/apps/evaluations/serializers.py`
- **Endpoints involved**
  - `POST /api/evaluations/transcripts/<transcript_id>/generate-summary/`
  - `PATCH /api/evaluations/interview-summaries/<summary_id>/`
- **Tests added/confirmed**
  - Mock summary default, required summary fields, missing API-key fallback, provider-failure fallback, and interviewer edit flow are covered in `backend/apps/interviews/tests.py`.
- **Current limitations**
  - The current persisted `communication_score` uses a 0-10 scale for compatibility, while some algorithm examples discuss broader 0-100 scoring.
  - Mock summaries are generic and do not deeply analyze transcript content.
- **Fallback behavior**
  - Real summary is disabled by default.
  - Missing API key or provider failure returns a deterministic structured mock summary with editable fields.
- **Future enhancement**
  - Decide whether to migrate communication score to 0-100 and update models, serializers, frontend, tests, and report together.
  - Add optional local LLM or explicitly configured provider integration only after preserving the mock fallback path.
- **Manual test steps**
  1. Generate a transcript for an interview recording.
  2. Call `POST /api/evaluations/transcripts/<transcript_id>/generate-summary/`.
  3. Verify strengths, weaknesses, communication score, overall impression, and editable summary text.
  4. Call `PATCH /api/evaluations/interview-summaries/<summary_id>/` and confirm edited fields are saved.

## External API safety

- Resume screening does not use OpenAI.
- Semantic matching uses optional Sentence-BERT only; failures fall back locally.
- Transcription and summary services call OpenAI helper methods only when explicitly enabled and configured. Regression tests patch these helper methods for provider-failure paths and assert disabled/default paths do not call them.
- Test cases use local generated PDFs/DOCX files, local database records, and mocked provider calls only.

## Remaining gaps before final FYP demo

1. **Scanned resume OCR is not supported.** Use text-based PDF/DOCX demo resumes, or add optional OCR later.
2. **Skill dictionary coverage is finite.** Add the exact skills expected in demo jobs and resumes before the final presentation.
3. **Semantic fallback is lexical, not truly semantic.** For best demo quality, either install/cache Sentence-BERT locally or prepare resumes/job descriptions with overlapping relevant keywords.
4. **Mock interview transcript and summary are intentionally generic.** This is reliable for demo stability, but realistic transcript/summary generation requires an explicitly configured provider or local model.
5. **Communication score remains 0-10.** Keep frontend/backend messaging consistent, or plan a coordinated migration after the demo.
6. **AI is advisory only.** Recruiter shortlist/reject decisions and HR approval decisions must still be demonstrated manually after AI screening.
