"""Shared preprocessing helpers for resume and job matching text.

These helpers intentionally return normalized copies for matching/scoring only.
Callers should keep original parsed resume/job text for display and persistence.
"""

import re


_WORD_PUNCTUATION_PATTERN = re.compile(r'[^A-Za-z0-9+#.]+')
_WHITESPACE_PATTERN = re.compile(r'\s+')


def coerce_text(value):
    """Return a safe text value for preprocessing.

    ``None`` becomes an empty string, strings are preserved, and other input is
    converted with ``str`` so service callers do not crash on unexpected values.
    """
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return str(value)


def normalize_whitespace(value):
    """Collapse repeated whitespace into single spaces and trim the result."""
    return _WHITESPACE_PATTERN.sub(' ', coerce_text(value)).strip()


def safe_lower(value):
    """Lowercase text safely for deterministic matching."""
    return coerce_text(value).lower()


def cleanup_punctuation(value, preserve_skill_symbols=True):
    """Replace punctuation with spaces while preserving useful skill symbols.

    By default this keeps ``+``, ``#``, and ``.`` because common skill names and
    aliases such as ``C++``, ``C#``, ``React.js``, and ``Node.js`` depend on them.
    """
    text = coerce_text(value)
    if preserve_skill_symbols:
        return _WORD_PUNCTUATION_PATTERN.sub(' ', text)
    return re.sub(r'[^\w\s]+', ' ', text)


def normalize_tokens(value, lowercase=True, cleanup=True, preserve_skill_symbols=True):
    """Normalize tokens for extraction and scoring comparisons."""
    text = coerce_text(value)
    if lowercase:
        text = safe_lower(text)
    if cleanup:
        text = cleanup_punctuation(text, preserve_skill_symbols=preserve_skill_symbols)
    return normalize_whitespace(text)


def preprocess_for_matching(value):
    """Return normalized text for skill, education, and experience matching."""
    return normalize_tokens(value, lowercase=True, cleanup=True, preserve_skill_symbols=True)


def preprocess_for_semantic_matching(value):
    """Return normalized text for semantic matching without mutating display text."""
    return normalize_tokens(value, lowercase=True, cleanup=True, preserve_skill_symbols=True)
