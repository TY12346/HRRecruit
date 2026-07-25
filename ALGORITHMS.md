# HRRecruit AI Algorithm Implementation Requirements

This file converts the FYP algorithm design into practical backend implementation requirements for HRRecruit.

Traceability: `ALGORITHMS.md` is derived from `ALGORITHMS_SOURCE.md`, which is the source reference for AI-related algorithm design. Future AI-related backend implementation should follow this file while preserving the intent and constraints from `ALGORITHMS_SOURCE.md`.

AI features in HRRecruit must support recruiter, interviewer, and hiring manager decision-making. They must not automatically make final hiring, rejection, or approval decisions.

---

## 1. Resume Skill Extraction using spaCy

### Purpose

Convert an uploaded resume into structured applicant information for resume screening, scoring, and ranking.

### Input

- `resume_file`
- `applicant_id`

Supported resume formats:

- PDF
- DOCX

### Processing Steps

1. Load the resume file for the specified applicant.
2. Validate that the file exists and is an allowed resume type.
3. Extract raw text from the PDF or DOCX file.
4. Clean and normalize the extracted text.
5. Process the cleaned text with spaCy when available.
6. Extract skills using spaCy together with practical matching rules.
7. Normalize extracted skill names so equivalent terms are stored consistently.
8. Extract education information using keyword and rule-based matching.
9. Extract experience information using regex and rule-based matching.
10. Return and store the structured extraction result.

### Practical spaCy Requirement

The FYP algorithm design references entity labels such as `SKILL` and `EDUCATION`. Standard spaCy `en_core_web_sm` may not provide custom `SKILL` or `EDUCATION` labels by default. Therefore, the practical implementation may use:

- spaCy `en_core_web_sm` text processing
- spaCy `PhraseMatcher` or `Matcher`
- predefined skill dictionaries
- skill normalization maps
- education keyword rules
- regex-based experience extraction

Example skill normalization rules may include:

```text
py -> Python
js -> JavaScript
reactjs -> React
nodejs -> Node.js
postgres -> PostgreSQL
```

Education extraction should look for relevant keywords such as:

```text
Bachelor
Degree
Diploma
Master
PhD
Computer Science
Software Engineering
Information Technology
```

Experience extraction should detect patterns such as:

```text
2 years experience
3+ years
software engineer at ABC Company
internship
worked as developer
```

### Output

The extraction result should include:

- `parsed_text`
- `extracted_skills`
- `extracted_education`
- `extracted_experience`

### Storage Requirement

Store or expose the extracted data in a suitable model based on the current backend design, such as a resume extraction model, applicant profile, application score explanation, or related application screening record.

---

## 2. Resume and Job Requirement Semantic Matching using Sentence-BERT

### Purpose

Calculate how semantically similar a applicant resume is to a job description and job requirements. This helps match applicants and jobs even when they use different wording for similar concepts.

### Input

- `job_id`
- `applicant_id`
- `job_description`
- `job_requirements`
- `resume_text`

### Processing Steps

1. Load the job description and job requirements.
2. Load the applicant resume text.
3. Clean and preprocess both job text and resume text.
4. If `sentence-transformers` and the model are available, load Sentence-BERT.
5. Generate embeddings for the job text and resume text.
6. Compute cosine similarity between the embeddings.
7. Normalize the similarity score to a 0-100 scale.
8. Return and store the `semantic_score`.
9. Avoid reloading the model unnecessarily on every request.
10. Do not use OpenAI for semantic matching.

### Required Model

Sentence-BERT should use `all-MiniLM-L6-v2` when available. Acceptable model references are:

```text
sentence-transformers/all-MiniLM-L6-v2
all-MiniLM-L6-v2
```

### Fallback Requirement

If `sentence-transformers` is unavailable, the model cannot be downloaded, or local model loading fails, the application must use a safe fallback score instead of crashing.

Fallback behavior may use a simple local method supported by `ALGORITHMS_SOURCE.md`, such as:

- keyword overlap
- Jaccard similarity
- simple token similarity
- safe mock score

The fallback must be deterministic enough for FYP development and demo reliability where practical.

### Output

- `semantic_score`

The score must use this scale:

```text
0 = no match
100 = excellent match
```

### Storage Requirement

Store or expose `semantic_score` in the application screening result, applicant ranking record, score explanation JSON, or another suitable scoring model based on the current backend design.

---

## 3. AI Applicant Ranking using Hybrid Scoring Model

### Purpose

Combine semantic, skill, experience, and education matching signals into one final applicant score for recruiter review.

The ranking must support recruiter decision-making and must not replace human shortlisting or rejection decisions.

### Input

- `applicant_data`
- `job_requirements`
- `semantic_score`
- `skill_score`
- `experience_score`
- `education_score`

### Processing Steps

1. Load the applicant profile and extracted resume data.
2. Load the job requirements.
3. Calculate or retrieve `semantic_score` from Sentence-BERT semantic matching or fallback semantic matching.
4. Calculate `skill_score` by comparing extracted applicant skills with job skill requirements and any requirement weights.
5. Identify `matched_skills` and `missing_skills`.
6. Calculate `experience_score` by comparing extracted applicant experience with the job experience requirement.
7. Identify `experience_match` and `experience_gap`.
8. Calculate `education_score` by comparing extracted applicant education with the job education requirement.
9. Identify `education_match` and `education_gap`.
10. Calculate `final_score` using the required formula.
11. Store the final score and score explanation.
12. Rank applicants by final score in descending order.
13. Use a stable secondary ordering such as `applied_at` ascending when scores are equal.

### Required Final Scoring Formula

Use this formula exactly:

```text
final_score = 0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score
```

### Component Score Scale

All component scores and the final score must use a 0-100 scale:

- `semantic_score`
- `skill_score`
- `experience_score`
- `education_score`
- `final_score`

### Output

- `final_score`
- `ranked_applicants`
- `score_explanation`

### Storage Requirement

Store `final_score` and a `score_explanation` JSON object. The explanation should include the formula, component scores, matched and missing skills, education match details, experience match details, and human-readable notes where available.

Example structure:

```json
{
  "formula": "0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score",
  "semantic_score": 82.5,
  "skill_score": 75.0,
  "experience_score": 60.0,
  "education_score": 80.0,
  "final_score": 75.5,
  "matched_skills": ["Python", "Django", "PostgreSQL"],
  "missing_skills": ["React"],
  "education_match": true,
  "experience_match": false,
  "notes": "Applicant has strong backend skills but lacks React experience."
}
```

### Application Status Requirement

AI screening automatically separates qualified and underqualified applicants. Qualified applicants remain in recruiter review, while underqualified applicants are rejected due to the screening threshold.

```text
If final_score >= threshold:
    status = shortlisted
else:
    status = rejected
```

The recruiter may still review AI-shortlisted applicants and decide whether they should be:

- assigned to an interviewer
- rejected
- given an additional recruiter remark

---

## 4. Automatic Speech Recognition for Interview Audio Transcription

### Purpose

Convert interview audio recordings into text transcripts for later interview summarization.

### Input

- `interview_id`
- `audio_file`

### Processing Steps

1. Load the interview audio file.
2. Validate that the audio file exists.
3. Validate that the audio file type is allowed.
4. Optionally preprocess the audio.
5. If real transcription is enabled and available, use Whisper or another ASR service.
6. If real transcription is disabled or unavailable, use mock transcription.
7. Post-process the transcript.
8. Save the transcript.
9. Return the cleaned transcript.

### Real Transcription and Mock Fallback Requirement

ASR should support real transcription later, but must keep mock fallback behavior for FYP development.

Real transcription should be optional because FYP development and demos must not fail when:

- an OpenAI API key is missing
- Whisper is not installed
- audio preprocessing fails
- internet is unavailable

Recommended environment variables:

```env
USE_REAL_TRANSCRIPTION=False
OPENAI_API_KEY=
TRANSCRIPTION_MODEL=whisper-1
```

If real transcription is disabled or unavailable, return a mock transcript such as:

```text
This is a mock interview transcript for FYP development.
```

### Output

- `cleaned_transcript`

### Storage Requirement

Save the transcript, including mock transcripts, in the database or suitable interview transcript storage so the interview evaluation and AI summary flow can continue during FYP development.

---

## 5. AI Interview Summarization

### Purpose

Generate a structured summary from an interview transcript so recruiters and interviewers can review interview performance more efficiently.

The summary must support human evaluation and must not automatically make hiring decisions.

### Input

- `interview_id`
- `transcript`

### Processing Steps

1. Load the interview transcript.
2. Clean and preprocess the transcript text.
3. Construct a structured prompt when real summary generation is enabled.
4. If real summary generation is enabled and available, call the configured language model provider (`openai` or `gemini`).
5. If real summary generation is disabled or unavailable, use a mock structured summary.
6. Validate that all required summary fields exist.
7. Save the structured summary.
8. Allow the interviewer to edit the summary before final submission.
9. Return the structured summary.

### Required Structured Fields

The AI summary should return these structured fields:

- `strengths`
- `weaknesses`
- `communication_score`
- `overall_impression`
- `editable_summary_text`

### Real Summary and Mock Fallback Requirement

For FYP development, real LLM summary generation should be optional. Mock/fallback summary behavior must remain available for FYP demo reliability.

Recommended environment variables for mock/demo mode and real provider selection:

```env
USE_REAL_SUMMARY=False
SUMMARY_PROVIDER=gemini
GEMINI_API_KEY=
OPENAI_API_KEY=
SUMMARY_MODEL=gemini-3.5-flash
```

Set `USE_REAL_SUMMARY=True` and `SUMMARY_PROVIDER=gemini` to generate interview AI summaries through Google Gemini. Set `SUMMARY_PROVIDER=openai` to keep the earlier OpenAI path. Both real providers must still return the required editable JSON fields and must not make hiring decisions.

If real summary is disabled or unavailable, return a structured mock summary such as:

```json
{
  "strengths": "The applicant shows relevant experience and communicates clearly.",
  "weaknesses": "The applicant may need further evaluation on technical depth.",
  "communication_score": 75,
  "overall_impression": "The applicant appears suitable for further consideration.",
  "editable_summary_text": "Mock AI summary generated for FYP development."
}
```

### Output

- `formatted_summary`

The returned summary must include all required structured fields.

### Storage Requirement

Store the structured summary in the interview evaluation or interview summary model according to the current backend design. Store `editable_summary_text` so interviewers can revise the summary before final submission.

---

## 6. General AI Implementation Rules

### Human Decision Rule

AI must support human decision-making and must not automatically make final hiring decisions. Recruiters, interviewers, and hiring managers remain responsible for recruitment decisions, interview evaluations, hiring decisions, and final approvals.

### Service Layer Rule

AI logic should stay inside service files, not directly inside views.

Use service files such as:

```text
ai_services/resume_text_extractor.py
ai_services/resume_preprocessor.py
ai_services/skill_extractor.py
ai_services/education_extractor.py
ai_services/experience_extractor.py
ai_services/semantic_matcher.py
ai_services/applicant_scoring.py
ai_services/transcription_service.py
ai_services/summary_service.py
```

Views should validate requests, enforce permissions, call services, and return clean JSON responses. They should not contain the core AI algorithms.

### Fallback and Demo Reliability Rule

Mock/fallback behavior must remain available for FYP demo reliability. Every AI-related service should have safe fallback behavior where practical so the application does not crash because:

- an API key is missing
- a model is not installed
- internet is unavailable
- a file is unreadable
- real transcription or real summary generation is disabled

Fallback behavior should still save useful mock or fallback outputs when required so downstream flows can continue.

### Testing Rule

AI services should be independently testable. Add tests for important AI business flows when implementing backend code, including:

- resume text extraction
- skill extraction
- skill normalization
- education extraction
- experience extraction
- semantic score normalization
- hybrid scoring formula
- ranking order
- mock transcription
- mock summary
- summary editing

### Documentation Rule

After implementing AI backend features, create or update `AI_ALGORITHM_VALIDATION_REPORT.md` to map each algorithm to:

- implemented files
- endpoints involved
- tests added
- known limitations
- fallback behavior
- future enhancement

## Interview transcription with optional speaker diarization

1. HRRecruit runs the configured speech-to-text provider. Local Whisper is the default real provider and can return timestamped transcript segments.
2. Speaker diarization is a separate optional local layer that detects speaker turns such as `SPEAKER_00` with start and end timestamps.
3. HRRecruit aligns Whisper transcript segments to diarization turns by selecting the speaker turn with the largest timestamp overlap.
4. HRRecruit maps internal speaker ids to the user-facing interview roles `Interviewer` and `Applicant`. The role mapping favors the speaker who asks the most questions or uses recruiter/HR/interviewer language as `Interviewer`, and maps the other primary speaker to `Applicant`.
5. `InterviewTranscript.transcript_text` stores the readable transcript. When diarization succeeds this is speaker-labelled text; otherwise it remains the plain transcript.
6. `InterviewTranscript.transcript_json` stores the plain transcript, optional speaker-labelled transcript, diarization status/warning, and structured speaker segments.
7. If diarization dependencies are missing or fail, the system must fall back to plain transcript mode and preserve AI summary compatibility.
