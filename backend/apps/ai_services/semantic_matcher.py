"""Semantic similarity helpers with a fast local fallback for early development."""

from functools import lru_cache

from django.conf import settings

from .resume_preprocessor import preprocess_for_semantic_matching


DEFAULT_MODEL_NAME = 'all-MiniLM-L6-v2'


# Keep this tuple intentionally broad enough to cover the common failure modes
# from optional ML dependencies (missing imports, offline model downloads, tensor
# operations, and runtime execution errors) while leaving process-level exceptions
# such as KeyboardInterrupt/SystemExit untouched.
_SENTENCE_BERT_FAILURES = (
    ImportError,
    ModuleNotFoundError,
    OSError,
    RuntimeError,
    ValueError,
    TypeError,
    AttributeError,
    IndexError,
    KeyError,
)


def semantic_similarity(resume_text, job_description):
    """Return a 0-100 semantic match score without blocking applicant flows.

    Sentence-BERT is optional in this project. By default, HRRecruit uses a
    deterministic token-overlap score so applicant job applications do not hang
    while a local machine downloads or loads ML models. Set
    ``AI_USE_SENTENCE_BERT=True`` to opt into the local Sentence-BERT path; if
    that optional path fails, the same fast fallback is used.
    """

    normalized_resume_text = preprocess_for_semantic_matching(resume_text)
    normalized_job_description = preprocess_for_semantic_matching(job_description)

    if not normalized_resume_text or not normalized_job_description:
        return 0.0

    if getattr(settings, 'AI_USE_SENTENCE_BERT', False):
        try:
            return _sentence_bert_similarity(normalized_resume_text, normalized_job_description)
        except _SENTENCE_BERT_FAILURES:
            return _token_overlap_similarity(normalized_resume_text, normalized_job_description)

    return _token_overlap_similarity(normalized_resume_text, normalized_job_description)


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


def _token_overlap_similarity(normalized_resume_text, normalized_job_description):
    resume_tokens = set(normalized_resume_text.split())
    job_tokens = set(normalized_job_description.split())
    if not resume_tokens or not job_tokens:
        return 0.0

    overlap = len(resume_tokens & job_tokens)
    # Sørensen-Dice gives a stable local approximation without optional ML deps.
    return round((2 * overlap / (len(resume_tokens) + len(job_tokens))) * 100, 2)


def _normalize_score(score):
    """Clamp a 0-1 similarity value and return a rounded 0-100 score."""
    return round(max(0.0, min(100.0, float(score) * 100)), 2)


def _validate_score(score, name):
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise TypeError(f'{name} must be a number.')
    if not 0 <= score <= 100:
        raise ValueError(f'{name} must be between 0 and 100.')
