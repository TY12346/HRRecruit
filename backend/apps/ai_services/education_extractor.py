"""Rule-based education extraction for resume screening.

The extractor is intentionally deterministic and local so early FYP demos and
backend tests never depend on external AI services.  It keeps the historical
``level`` key while returning richer structured metadata required by
``ALGORITHMS.md``.
"""

import re

from .resume_preprocessor import coerce_text, normalize_whitespace, preprocess_for_matching


EDUCATION_LEVELS = {
    'secondary': 1,
    'diploma': 2,
    'associate': 2,
    'bachelor': 3,
    'master': 4,
    'doctorate': 5,
}

EDUCATION_LEVEL_LABELS = {
    'secondary': 'Secondary',
    'diploma': 'Diploma',
    'associate': 'Associate',
    'bachelor': 'Bachelor',
    'master': 'Master',
    'doctorate': 'Doctorate',
}

EDUCATION_ALIASES = {
    'doctorate': (
        ('doctorate', 'Doctorate'),
        ('doctoral', 'Doctoral'),
        ('phd', 'PhD'),
        ('ph.d', 'PhD'),
        ('ph.d.', 'PhD'),
    ),
    'master': (
        ('master', 'Master'),
        ("master's", 'Master'),
        ('masters', 'Master'),
        ('msc', 'Master'),
        ('m.sc', 'Master'),
        ('m.sc.', 'Master'),
        ('mba', 'Master'),
    ),
    'bachelor': (
        ('bachelor', 'Bachelor'),
        ("bachelor's", 'Bachelor'),
        ('bachelors', 'Bachelor'),
        ('bsc', 'Bachelor'),
        ('b.sc', 'Bachelor'),
        ('b.sc.', 'Bachelor'),
    ),
    'associate': (
        ('associate degree', 'Associate'),
        ('associate', 'Associate'),
    ),
    'diploma': (
        ('diploma', 'Diploma'),
    ),
    'secondary': (
        ('secondary school', 'Secondary'),
        ('high school', 'Secondary'),
        ('spm', 'Secondary'),
    ),
}

EDUCATION_KEYWORDS = (
    ('degree', 'Degree'),
)

FIELDS_OF_STUDY = {
    'Computer Science': ('computer science', 'computing science', 'cs'),
    'Software Engineering': ('software engineering',),
    'Information Technology': ('information technology', 'it'),
}


def extract_education(text):
    """Return structured education details extracted from free-form text.

    The ``level`` key preserves the previous API/test contract.  Additional
    keys expose the matched education label, fields of study, detected keywords,
    and raw mention snippets for recruiter-facing explanations.
    """
    raw_text = coerce_text(text)
    normalized_text = preprocess_for_matching(raw_text)

    level_matches = []
    matched_keywords = []
    raw_mentions = []

    for level, aliases in EDUCATION_ALIASES.items():
        for alias, label in aliases:
            if _contains_alias(normalized_text, alias):
                level_matches.append(level)
                _append_unique(matched_keywords, label)
                _append_unique(raw_mentions, _best_raw_mention(raw_text, alias, label))

    for alias, label in EDUCATION_KEYWORDS:
        if _contains_alias(normalized_text, alias):
            _append_unique(matched_keywords, label)
            _append_unique(raw_mentions, _best_raw_mention(raw_text, alias, label))

    fields_of_study = []
    for field_label, aliases in FIELDS_OF_STUDY.items():
        for alias in aliases:
            if _contains_alias(normalized_text, alias):
                _append_unique(fields_of_study, field_label)
                _append_unique(matched_keywords, field_label)
                _append_unique(raw_mentions, _best_raw_mention(raw_text, alias, field_label))
                break

    level = max(level_matches, key=EDUCATION_LEVELS.get) if level_matches else None
    return {
        'level': level,
        'level_label': EDUCATION_LEVEL_LABELS.get(level),
        'fields_of_study': fields_of_study,
        'matched_keywords': matched_keywords,
        'raw_mentions': raw_mentions,
    }


def _contains_alias(normalized_text, alias):
    normalized_alias = preprocess_for_matching(alias)
    if not normalized_alias:
        return False
    pattern = rf'(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])'
    return bool(re.search(pattern, normalized_text))


def _best_raw_mention(raw_text, alias, fallback):
    raw_text = coerce_text(raw_text)
    normalized_alias = normalize_whitespace(alias)
    escaped_words = [re.escape(part) for part in re.split(r'\s+', normalized_alias) if part]
    if escaped_words:
        pattern = r'(?<![A-Za-z0-9])' + r'\s+'.join(escaped_words) + r'(?![A-Za-z0-9])'
        match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        if match:
            return normalize_whitespace(match.group(0))
    return fallback


def _append_unique(values, value):
    if value and value not in values:
        values.append(value)
