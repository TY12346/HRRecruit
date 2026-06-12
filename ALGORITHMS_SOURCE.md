# HRRecruit Algorithms Source

This file is the source reference for implementing the AI-related algorithms in HRRecruit.

Use this file to create or update `ALGORITHMS.md`.

## Important Context

These algorithm requirements are based on the FYP algorithm design section.

They should be used together with:

- `AGENTS.md`
- `FYP_REQUIREMENTS_SUMMARY.md`
- `CODEX_PROMPTS.md`

Important rule:

- The written algorithm requirements in this file are authoritative for AI-related features.
- Do not follow the incorrect Chapter 4 diagrams.
- AI features should support human decision-making.
- AI must not automatically make final hiring or rejection decisions.

---

# 1. Resume Skill Extraction Using spaCy

## Purpose

This algorithm converts an unstructured resume document into structured candidate information.

It should extract:

- Resume text
- Skills
- Education information
- Experience information

The extracted information will be used later for resume screening, candidate scoring, and candidate ranking.

## Input

```text
resume_file
candidate_id
```

The resume file may be:

```text
PDF
DOCX
```

## Output

```text
normalized_skills
education
experience
parsed_text
```

## High-Level Pseudocode

```python
# Step 1: Input resume document
resume_text = extract_text_from_file(resume_file)

# Step 2: Pre-processing
cleaned_text = preprocess_text(resume_text)

# Step 3: Load NLP Model
nlp_model = load_spacy_model("en_core_web_sm")

# Step 4: Named Entity Recognition / NLP Processing
doc = nlp_model(cleaned_text)

# Step 5: Extract Relevant Entities
skills = extract_entities(doc, label="SKILL")
education = extract_entities(doc, label="EDUCATION")
experience = extract_experience_patterns(doc)

# Step 6: Normalize Extracted Data
normalized_skills = normalize_skills(skills)

# Step 7: Store Extracted Information
save_candidate_profile(candidate_id, normalized_skills, education, experience)

# Step 8: Output Extracted Data
return normalized_skills, education, experience
```

## Practical Implementation Notes

The FYP pseudocode uses labels such as `SKILL` and `EDUCATION`.

However, the default spaCy model `en_core_web_sm` may not automatically detect custom entities such as `SKILL` and `EDUCATION`.

Therefore, the implementation should use a practical FYP-friendly approach:

```text
spaCy text processing
+ PhraseMatcher / Matcher
+ predefined skill dictionary
+ education keyword rules
+ experience regex/rules
+ normalization map
```

## Required Implementation Behavior

The implementation should:

1. Load the resume file.
2. Extract raw text from PDF or DOCX.
3. Clean and normalize the text.
4. Process text using spaCy if available.
5. Extract skills using a skills dictionary and spaCy matcher.
6. Normalize skill names.

Example normalization:

```text
py -> Python
js -> JavaScript
reactjs -> React
nodejs -> Node.js
postgres -> PostgreSQL
```

7. Extract education using keyword/rule-based matching.

Examples of education keywords:

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

8. Extract experience using regex/rule-based matching.

Examples:

```text
2 years experience
3+ years
software engineer at ABC Company
internship
worked as developer
```

9. Return and/or store structured extraction results.

## Storage Requirement

The system should store or expose:

```text
parsed_text
extracted_skills
extracted_education
extracted_experience
```

These may be stored in a resume extraction model, candidate profile, application score explanation, or another existing suitable model depending on the current codebase design.

---

# 2. Resume and Job Requirement Semantic Matching Using Sentence-BERT

## Purpose

This algorithm calculates how semantically similar a candidate resume is to a job posting or job requirements.

It helps HRRecruit match candidates even when the resume and job posting use different wording.

Example:

```text
"software engineer" and "developer"
```

These may not be exact keyword matches, but they are semantically similar.

## Input

```text
job_id
candidate_id
job_description
job_requirements
resume_text
```

## Output

```text
semantic_score
```

The score should be normalized to a 0–100 scale.

## High-Level Pseudocode

```python
# Step 1: Input Data
job_text = load_job_description(job_id)
resume_text = load_resume(candidate_id)

# Step 2: Pre-processing
cleaned_job_text = preprocess_text(job_text)
cleaned_resume_text = preprocess_text(resume_text)

# Step 3: Load Pre-trained Sentence-BERT Model
model = load_sbert_model("all-MiniLM-L6-v2")

# Step 4: Generate Embeddings
job_embedding = model.encode(cleaned_job_text)
resume_embedding = model.encode(cleaned_resume_text)

# Step 5: Compute Cosine Similarity
similarity_score = cosine_similarity(job_embedding, resume_embedding)

# Step 6: Normalize Score
normalized_score = normalize_score(similarity_score)

# Step 7: Output Matching Score
return normalized_score
```

## Required Model

Use:

```text
sentence-transformers/all-MiniLM-L6-v2
```

or:

```text
all-MiniLM-L6-v2
```

## Practical Implementation Notes

For FYP development, the system must not crash if the model is not installed or cannot be downloaded.

The implementation should support fallback behavior:

```text
If sentence-transformers is installed and model is available:
    use Sentence-BERT embeddings + cosine similarity
else:
    use a simple fallback similarity score for local development
```

Possible fallback methods:

```text
keyword overlap
Jaccard similarity
simple token similarity
safe mock score
```

## Required Implementation Behavior

The implementation should:

1. Load job text.
2. Load resume text.
3. Preprocess both texts.
4. Generate embeddings using Sentence-BERT if available.
5. Compute cosine similarity.
6. Convert the similarity to a percentage score from 0 to 100.
7. Return `semantic_score`.
8. Keep model loading efficient and avoid reloading the model unnecessarily on every request.
9. Avoid using OpenAI for semantic matching.

## Score Scale

All scores should use a consistent scale:

```text
0 = no match
100 = excellent match
```

---

# 3. AI Candidate Ranking Using Hybrid Scoring Model

## Purpose

This algorithm combines multiple candidate-job matching signals into one final score.

It is used to rank candidates for recruiters.

The ranking should support recruiter decision-making, not replace it.

## Input

```text
candidate_data
job_requirements
semantic_score
skill_score
experience_score
education_score
```

## Output

```text
final_score
ranked_candidates
score_explanation
```

## High-Level Pseudocode

```python
# Step 1: Input Data
candidate_data = load_candidate_profile(candidate_id)
job_requirements = load_job_requirements(job_id)

# Step 2: Compute Semantic Similarity Score
semantic_score = get_sbert_similarity(candidate_id, job_id)

# Step 3: Compute Skill Matching Score
skill_score = calculate_weighted_skill_match(
    candidate_data.skills,
    job_requirements.skills,
    job_requirements.skill_weights
)

# Step 4: Compute Experience Score
experience_score = calculate_experience_match(
    candidate_data.experience,
    job_requirements.experience_required
)

# Step 5: Compute Education Score
education_score = calculate_education_match(
    candidate_data.education,
    job_requirements.education_required
)

# Step 6: Aggregate Final Score
final_score = (
    0.4 * semantic_score +
    0.3 * skill_score +
    0.2 * experience_score +
    0.1 * education_score
)

# Step 7: Store Final Score
store_final_score(candidate_id, final_score)

# Step 8: Output Final Score
return final_score
```

## Required Final Score Formula

Use this exact formula:

```text
final_score = 0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score
```

## Component Scores

All component scores must use a 0–100 scale:

```text
semantic_score
skill_score
experience_score
education_score
final_score
```

## Skill Score

The skill score should compare:

```text
candidate extracted skills
job skill requirements
requirement weights
```

The implementation should identify:

```text
matched_skills
missing_skills
```

## Experience Score

The experience score should compare:

```text
candidate extracted experience
job experience requirements
```

The implementation should identify:

```text
experience_match
experience_gap
```

## Education Score

The education score should compare:

```text
candidate extracted education
job education requirements
```

The implementation should identify:

```text
education_match
education_gap
```

## Score Explanation

The system should store a `score_explanation` JSON object.

Example:

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
  "notes": "Candidate has strong backend skills but lacks React experience."
}
```

## Required Application Status Behavior

The AI screening result automatically rejects underqualified applicants and keeps qualified applicants available for recruiter review.

Use this behavior:

```text
If final_score >= threshold:
    status = screened_qualified
else:
    status = rejected
```

Underqualified applicants are rejected automatically by the screening threshold. The recruiter must manually decide whether qualified applicants should be:

```text
assign interviewer
reject
add remark
```

## Ranking Behavior

Rank candidates by:

```text
final_score descending
```

If scores are equal, use a stable secondary ordering such as:

```text
applied_at ascending
```

---

# 4. Automatic Speech Recognition for Interview Audio Transcription

## Purpose

This algorithm converts interview audio recordings into text transcripts.

The transcript is later used for AI interview summarization.

## Input

```text
interview_id
audio_file
```

## Output

```text
cleaned_transcript
```

## High-Level Pseudocode

```python
# Step 1: Input Audio File
audio_file = load_audio(interview_id)

# Step 2: Pre-process Audio
processed_audio = preprocess_audio(audio_file)

# Step 3: Load ASR Model
asr_model = load_asr_model("whisper")

# Step 4: Transcribe Audio
transcript = asr_model.transcribe(processed_audio)

# Step 5: Post-process Transcript
cleaned_transcript = postprocess_transcript(transcript)

# Step 6: Store Transcript
save_transcript(interview_id, cleaned_transcript)

# Step 7: Output Transcript
return cleaned_transcript
```

## Practical Implementation Notes

For FYP development, real transcription should be optional.

The system should keep mock transcription as fallback.

This avoids blocking the whole project if:

```text
OpenAI API key is missing
Whisper is not installed
audio preprocessing fails
internet is unavailable
```

## Required Implementation Behavior

The transcription implementation should:

1. Load interview audio file.
2. Validate file exists.
3. Validate allowed audio type.
4. Optionally preprocess audio.
5. If real transcription is enabled, use Whisper or another ASR service.
6. If real transcription is disabled or unavailable, use mock transcription.
7. Post-process the transcript.
8. Save the transcript.
9. Return the transcript.

## Environment Variables

Recommended:

```env
USE_REAL_TRANSCRIPTION=False
OPENAI_API_KEY=
TRANSCRIPTION_MODEL=whisper-1
```

## Mock Fallback Behavior

If real transcription is disabled, return a mock transcript such as:

```text
This is a mock interview transcript for FYP development.
```

The mock transcript should still be saved in the database so that the rest of the interview evaluation flow works.

---

# 5. AI Interview Summarization

## Purpose

This algorithm generates a structured summary from an interview transcript.

The summary helps recruiters and interviewers review interview performance more efficiently.

It should support human evaluation, not replace it.

## Input

```text
interview_id
transcript
```

## Output

```text
formatted_summary
```

The summary should include:

```text
strengths
weaknesses
communication_score
overall_impression
editable_summary_text
```

## High-Level Pseudocode

```python
# Step 1: Input Transcript
transcript = load_transcript(interview_id)

# Step 2: Pre-process Text
cleaned_text = preprocess_text(transcript)

# Step 3: Construct Prompt
summary_prompt = '''
Summarize the following interview transcript into:
1. Key strengths
2. Key weaknesses
3. Communication ability
4. Overall impression

Transcript:
''' + cleaned_text

# Step 4: Load Language Model
model = load_gpt_model("gpt-4")

# Step 5: Generate Summary
summary = model.generate(summary_prompt)

# Step 6: Post-process Output
formatted_summary = format_summary(summary)

# Step 7: Store Summary
save_summary(interview_id, formatted_summary)

# Step 8: Output Summary
return formatted_summary
```

## Practical Implementation Notes

For FYP development, real LLM summary generation should be optional.

The system should keep mock summary as fallback.

This avoids blocking the project if:

```text
OpenAI API key is missing
internet is unavailable
API quota is unavailable
```

## Required Implementation Behavior

The summarization implementation should:

1. Load transcript.
2. Preprocess transcript text.
3. Construct a structured prompt.
4. If real summary is enabled, call a language model.
5. If real summary is disabled or unavailable, use mock summary.
6. Validate that all required output fields exist.
7. Save the structured summary.
8. Allow interviewer to edit the summary before final submission.
9. Return the summary.

## Environment Variables

Recommended:

```env
USE_REAL_SUMMARY=False
OPENAI_API_KEY=
SUMMARY_MODEL=gpt-4o-mini
```

## Required Summary Fields

```text
strengths
weaknesses
communication_score
overall_impression
editable_summary_text
```

## Mock Fallback Behavior

If real summary is disabled, return a structured mock summary such as:

```json
{
  "strengths": "The candidate shows relevant experience and communicates clearly.",
  "weaknesses": "The candidate may need further evaluation on technical depth.",
  "communication_score": 75,
  "overall_impression": "The candidate appears suitable for further consideration.",
  "editable_summary_text": "Mock AI summary generated for FYP development."
}
```

## Human Decision Rule

The AI summary must not automatically make hiring decisions.

The recruiter and HR department head remain responsible for final decision-making.

---

# 6. General AI Implementation Rules

## Service Layer Rule

Do not place AI logic directly inside views.

Use service files such as:

```text
ai_services/resume_text_extractor.py
ai_services/resume_preprocessor.py
ai_services/skill_extractor.py
ai_services/education_extractor.py
ai_services/experience_extractor.py
ai_services/semantic_matcher.py
ai_services/candidate_scoring.py
ai_services/transcription_service.py
ai_services/summary_service.py
```

## Fallback Rule

Every AI-related service must have safe fallback behavior where practical.

The system should not crash during FYP demo just because:

```text
an API key is missing
a model is not installed
internet is unavailable
a file is unreadable
```

## Test Rule

AI services should be independently testable.

Add tests for:

```text
resume text extraction
skill extraction
skill normalization
education extraction
experience extraction
semantic score normalization
hybrid scoring formula
ranking order
mock transcription
mock summary
summary editing
```

## Documentation Rule

After implementation, create or update:

```text
AI_ALGORITHM_VALIDATION_REPORT.md
```

This report should map each algorithm to:

```text
implemented files
endpoints involved
tests added
known limitations
fallback behavior
future enhancement
```
