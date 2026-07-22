"""Sentence-BERT semantic similarity helpers."""

from functools import lru_cache

from .resume_preprocessor import preprocess_for_semantic_matching


DEFAULT_MODEL_NAME = 'all-MiniLM-L6-v2'


def semantic_similarity(resume_text, job_description):
    """Return a 0-100 Sentence-BERT semantic match score."""

    normalized_resume_text = preprocess_for_semantic_matching(resume_text)
    normalized_job_description = preprocess_for_semantic_matching(job_description)

    if not normalized_resume_text or not normalized_job_description:
        return 0.0

    return _sentence_bert_similarity(normalized_resume_text, normalized_job_description)


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
