"""Semantic similarity helpers with an optional sentence-transformers backend."""

from functools import lru_cache


DEFAULT_FALLBACK_SCORE = 50.0
DEFAULT_MODEL_NAME = 'all-MiniLM-L6-v2'


def semantic_similarity(resume_text, job_description, fallback_score=DEFAULT_FALLBACK_SCORE):
    """Return a 0-100 semantic match score or a mock fallback score.

    ``sentence-transformers`` is optional during early development. If it is not
    installed, this function returns ``fallback_score`` so callers remain fully
    testable without downloading a model or calling an external API.
    """
    _validate_score(fallback_score, 'fallback_score')

    if not str(resume_text or '').strip() or not str(job_description or '').strip():
        return 0.0

    try:
        model = _get_model()
    except (ImportError, ModuleNotFoundError):
        return float(fallback_score)

    embeddings = model.encode(
        [resume_text, job_description],
        convert_to_tensor=True,
        normalize_embeddings=True,
    )
    similarity = float((embeddings[0] @ embeddings[1]).item())
    return round(max(0.0, min(100.0, similarity * 100)), 2)


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(DEFAULT_MODEL_NAME)


def _validate_score(score, name):
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise TypeError(f'{name} must be a number.')
    if not 0 <= score <= 100:
        raise ValueError(f'{name} must be between 0 and 100.')
