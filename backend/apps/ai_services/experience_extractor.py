"""Rule-based experience extraction for resume screening.

This module keeps extraction deterministic and local while exposing richer
structured metadata than the original inlined year-only helper.
"""

import re

from .resume_preprocessor import coerce_text, normalize_whitespace, preprocess_for_matching


YEARS_PATTERN = re.compile(
    r'(?P<phrase>(?P<years>\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+(?:of\s+)?experience)?)',
    re.IGNORECASE,
)

ROLE_ALIASES = {
    'software engineer': ('software engineer', 'software developer'),
    'developer': ('developer',),
    'backend developer': ('backend developer', 'backend engineer'),
    'frontend developer': ('frontend developer', 'frontend engineer'),
    'full stack developer': ('full stack developer', 'full-stack developer', 'fullstack developer'),
    'data analyst': ('data analyst',),
    'data scientist': ('data scientist',),
    'mobile developer': ('mobile developer', 'flutter developer'),
    'qa engineer': ('qa engineer', 'quality assurance engineer', 'test engineer'),
    'project manager': ('project manager',),
    'business analyst': ('business analyst',),
    'intern': ('intern', 'internship'),
}

ROLE_PATTERN = '|'.join(
    re.escape(alias)
    for alias in sorted(
        (alias for aliases in ROLE_ALIASES.values() for alias in aliases),
        key=len,
        reverse=True,
    )
)

ROLE_AT_COMPANY_PATTERN = re.compile(
    rf'(?P<role>{ROLE_PATTERN})\s+at\s+(?P<company>[^\n,.;]+)',
    re.IGNORECASE,
)
WORKED_AS_PATTERN = re.compile(
    rf'worked\s+as\s+(?:an?\s+|the\s+)?(?P<role>{ROLE_PATTERN})',
    re.IGNORECASE,
)
INTERNSHIP_PATTERN = re.compile(
    r'(?P<phrase>\b(?:internship|intern)\b(?:\s+at\s+(?P<company>[^\n,.;]+))?)',
    re.IGNORECASE,
)


def extract_experience(text):
    """Return structured experience details extracted from free-form text.

    The historical ``years`` key is preserved for scoring/API compatibility.
    Additional keys describe role, company, internship, and matched phrase
    details for richer recruiter-facing explanations.
    """
    raw_text = normalize_whitespace(coerce_text(text))
    normalized_text = preprocess_for_matching(raw_text)

    year_values = []
    roles = []
    companies = []
    internships = []
    matched_phrases = []
    raw_mentions = []

    for match in YEARS_PATTERN.finditer(raw_text):
        year_values.append(float(match.group('years')))
        _record_phrase(match.group('phrase'), matched_phrases, raw_mentions)

    for match in ROLE_AT_COMPANY_PATTERN.finditer(raw_text):
        role = _canonical_role(match.group('role'))
        company = _clean_company(match.group('company'))
        _append_unique(roles, role)
        _append_unique(companies, company)
        _record_phrase(match.group(0), matched_phrases, raw_mentions)

    for match in WORKED_AS_PATTERN.finditer(raw_text):
        role = _canonical_role(match.group('role'))
        _append_unique(roles, role)
        _record_phrase(match.group(0), matched_phrases, raw_mentions)

    for match in INTERNSHIP_PATTERN.finditer(raw_text):
        phrase = match.group('phrase')
        company = _clean_company(match.group('company'))
        _append_unique(internships, phrase)
        _append_unique(roles, 'intern')
        if company:
            _append_unique(companies, company)
        _record_phrase(phrase, matched_phrases, raw_mentions)

    # If punctuation preprocessing removed separators before role detection,
    # still catch the explicit examples from ALGORITHMS.md in normalized text.
    if not roles and normalized_text:
        for canonical_role, aliases in ROLE_ALIASES.items():
            if any(_contains_alias(normalized_text, alias) for alias in aliases):
                _append_unique(roles, canonical_role)

    return {
        'years': max(year_values, default=0.0),
        'roles': roles,
        'companies': companies,
        'internships': internships,
        'matched_phrases': matched_phrases,
        'raw_mentions': raw_mentions,
    }


def _canonical_role(value):
    normalized_value = preprocess_for_matching(value)
    for canonical_role, aliases in ROLE_ALIASES.items():
        if any(normalized_value == preprocess_for_matching(alias) for alias in aliases):
            return canonical_role
    return normalized_value


def _clean_company(value):
    if not value:
        return ''
    company = normalize_whitespace(value).strip(' -')
    company = re.sub(r'\s+(?:as|for|where|using|with)\b.*$', '', company, flags=re.IGNORECASE).strip()
    return company


def _contains_alias(normalized_text, alias):
    normalized_alias = preprocess_for_matching(alias)
    if not normalized_alias:
        return False
    pattern = rf'(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])'
    return bool(re.search(pattern, normalized_text))


def _record_phrase(phrase, matched_phrases, raw_mentions):
    cleaned_phrase = normalize_whitespace(phrase)
    _append_unique(matched_phrases, cleaned_phrase)
    _append_unique(raw_mentions, cleaned_phrase)


def _append_unique(values, value):
    if value and value not in values:
        values.append(value)
