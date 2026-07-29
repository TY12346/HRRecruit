"""Sentence-BERT semantic similarity and human-readable evidence helpers."""

from functools import lru_cache
import re

from .resume_preprocessor import preprocess_for_semantic_matching


DEFAULT_MODEL_NAME = 'all-MiniLM-L6-v2'
MAX_RESUME_PASSAGES = 80
MAX_JOB_PASSAGES = 30
MAX_PASSAGE_LENGTH = 500
EVIDENCE_PER_REQUIREMENT = 2
DIFFERENT_WORDING_OVERLAP_THRESHOLD = 0.35
_STOP_WORDS = frozenset('a an and are as at be by for from in is it of on or the this to with you your'.split())


def semantic_similarity(resume_text, job_description):
    """Return a 0-100 Sentence-BERT semantic match score."""

    normalized_resume_text = preprocess_for_semantic_matching(resume_text)
    normalized_job_description = preprocess_for_semantic_matching(job_description)

    if not normalized_resume_text or not normalized_job_description:
        return 0.0

    return _sentence_bert_similarity(normalized_resume_text, normalized_job_description)


def split_passages(text, limit=MAX_RESUME_PASSAGES):
    """Return de-duplicated display/embedding passages without destroying C++/C# names."""
    text = str(text or '').replace('\r\n', '\n').replace('\r', '\n')
    candidates = re.split(r'\n\s*\n|\n\s*(?:[-*•‣▪]|\d+[.)])\s*|(?<=[.!?])\s+(?=[A-Z0-9])', text)
    passages, seen = [], set()
    for candidate in candidates:
        display = re.sub(r'\s+', ' ', candidate).strip(' \t-*•‣▪')[:MAX_PASSAGE_LENGTH]
        normalized = preprocess_for_semantic_matching(display)
        if len(display) < 20 or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        passages.append({'text': display, 'normalized_text': normalized})
        if len(passages) >= limit:
            break
    return passages


def build_semantic_analysis(resume_text, job_title, job_description, requirements):
    """Run one batched Sentence-BERT comparison and select genuine top evidence."""
    resume_passages = split_passages(resume_text, MAX_RESUME_PASSAGES)
    job_units = []
    if job_title:
        job_units.extend(_typed_passages(job_title, 'other', 'job_title'))
    job_units.extend(_typed_passages(job_description, 'other', 'job_description'))
    for requirement in requirements or []:
        description = getattr(requirement, 'description', None) or (requirement.get('description') if isinstance(requirement, dict) else '')
        requirement_type = getattr(requirement, 'requirement_type', None) or (requirement.get('requirement_type') if isinstance(requirement, dict) else 'other')
        job_units.extend(_typed_passages(description, requirement_type or 'other', 'configured_requirement'))
    job_units = job_units[:MAX_JOB_PASSAGES]
    full_job_text = ' '.join(unit['text'] for unit in job_units)
    normalized_resume = preprocess_for_semantic_matching(resume_text)
    normalized_job = preprocess_for_semantic_matching(full_job_text)
    empty = _analysis_payload(0.0, [])
    if not normalized_resume or not normalized_job:
        return empty

    # One encode call for the overall pair and all passage vectors; never one call per pair.
    texts = [normalized_resume, normalized_job]
    texts += [unit['normalized_text'] for unit in job_units]
    texts += [passage['normalized_text'] for passage in resume_passages]
    model = _get_model()
    embeddings = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    overall = _normalize_score(float((embeddings[0] @ embeddings[1]).item()))
    if not job_units or not resume_passages:
        return _analysis_payload(overall, [])
    job_start, resume_start = 2, 2 + len(job_units)
    similarities = embeddings[job_start:resume_start] @ embeddings[resume_start:].T
    evidence = []
    for job_index, unit in enumerate(job_units):
        row = similarities[job_index]
        ranked = sorted(range(len(resume_passages)), key=lambda index: float(row[index]), reverse=True)
        for rank, resume_index in enumerate(ranked[:EVIDENCE_PER_REQUIREMENT], 1):
            passage = resume_passages[resume_index]
            score = _normalize_score(float(row[resume_index]))
            shared_terms, different_wording = _lexical_evidence(unit['text'], passage['text'])
            evidence.append({
                'requirement_type': unit['requirement_type'], 'requirement_text': unit['text'],
                'requirement_source': unit['requirement_source'], 'resume_evidence': passage['text'],
                'similarity_score': score, 'different_wording': different_wording,
                'shared_terms': shared_terms, 'rank': rank,
            })
    return _analysis_payload(overall, evidence)


def _typed_passages(text, requirement_type, source):
    return [{**passage, 'requirement_type': str(requirement_type), 'requirement_source': source}
            for passage in split_passages(text, MAX_JOB_PASSAGES)]


def _lexical_evidence(requirement, evidence):
    def terms(value):
        return {token for token in re.findall(r'[a-z0-9+#.]+', value.lower()) if len(token) > 1 and token not in _STOP_WORDS}
    left, right = terms(requirement), terms(evidence)
    shared = sorted(left & right)
    overlap = len(shared) / max(1, min(len(left), len(right)))
    normalized_left = preprocess_for_semantic_matching(requirement)
    normalized_right = preprocess_for_semantic_matching(evidence)
    direct = normalized_left in normalized_right or normalized_right in normalized_left
    return shared, bool(not direct and overlap < DIFFERENT_WORDING_OVERLAP_THRESHOLD)


def _analysis_payload(overall_score, evidence_pairs):
    return {
        'engine': 'sentence-transformers', 'model_name': DEFAULT_MODEL_NAME,
        'algorithm': 'Sentence-BERT embeddings with cosine similarity',
        'overall_score': overall_score,
        'comparison_source': 'job title, description, and configured requirements',
        'evidence_pairs': evidence_pairs,
        'different_wording_match_count': sum(pair['different_wording'] for pair in evidence_pairs),
        'limitations': [
            'Semantic similarity indicates contextual relatedness, not verified competence.',
            'Resume evidence may be incomplete or ambiguous.', 'The result requires recruiter review.',
        ],
    }


def _sentence_bert_similarity(normalized_resume_text, normalized_job_description):
    model = _get_model()
    embeddings = model.encode(
        [normalized_resume_text, normalized_job_description],
        convert_to_tensor=True,
        normalize_embeddings=True,
    )
    similarity = float((embeddings[0] @ embeddings[1]).item())
    return _normalize_score(similarity)


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(DEFAULT_MODEL_NAME)


def _normalize_score(score):
    """Clamp a 0-1 similarity value and return a rounded 0-100 score."""
    return round(max(0.0, min(100.0, float(score) * 100)), 2)


def _validate_score(score, name):
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise TypeError(f'{name} must be a number.')
    if not 0 <= score <= 100:
        raise ValueError(f'{name} must be between 0 and 100.')
