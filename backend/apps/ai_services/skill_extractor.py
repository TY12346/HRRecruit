"""spaCy-capable skill extraction with deterministic fallback support."""

from functools import lru_cache
import importlib
import importlib.util
import re

from .resume_preprocessor import preprocess_for_matching


SKILLS_DICTIONARY = {
    'aws': ('amazon web services', 'aws'),
    'c#': ('c#', 'c sharp'),
    'c++': ('c++', 'cpp'),
    'css': ('css',),
    'django': ('django',),
    'docker': ('docker',),
    'flutter': ('flutter',),
    'git': ('git',),
    'html': ('html',),
    'java': ('java',),
    'javascript': ('javascript', 'java script', 'js'),
    'kubernetes': ('kubernetes', 'k8s'),
    'machine learning': ('machine learning', 'ml'),
    'mysql': ('mysql',),
    'node.js': ('node.js', 'nodejs', 'node js'),
    'postgresql': ('postgresql', 'postgres', 'postgre sql'),
    'python': ('python', 'py'),
    'react': ('react', 'react.js', 'reactjs'),
    'rest api': ('rest api', 'rest apis', 'restful api', 'restful apis'),
    'sql': ('sql',),
}

SKILL_DISPLAY_LABELS = {
    'aws': 'AWS',
    'c#': 'C#',
    'c++': 'C++',
    'css': 'CSS',
    'django': 'Django',
    'docker': 'Docker',
    'flutter': 'Flutter',
    'git': 'Git',
    'html': 'HTML',
    'java': 'Java',
    'javascript': 'JavaScript',
    'kubernetes': 'Kubernetes',
    'machine learning': 'Machine Learning',
    'mysql': 'MySQL',
    'node.js': 'Node.js',
    'postgresql': 'PostgreSQL',
    'python': 'Python',
    'react': 'React',
    'rest api': 'REST API',
    'sql': 'SQL',
}

SPACY_MODEL_NAME = 'en_core_web_sm'


def normalize_text(text):
    """Normalize free text while retaining symbols used in common skill names."""
    return preprocess_for_matching(text)


def extract_skills(text, skills_dictionary=None):
    """Return stable lower-case/internal skill keys found in text.

    spaCy with PhraseMatcher is used when spaCy and ``en_core_web_sm`` are
    available. If spaCy, the model, or matcher setup is unavailable, extraction
    falls back to the deterministic dictionary/regex matcher used by earlier
    versions so demo environments do not fail.
    """
    normalized_text = normalize_text(text)
    dictionary = SKILLS_DICTIONARY if skills_dictionary is None else skills_dictionary
    if not dictionary:
        return []

    spacy_skills = _extract_skills_with_spacy(normalized_text, dictionary)
    if spacy_skills is not None:
        return sorted(spacy_skills)

    return extract_skills_with_fallback(normalized_text, dictionary, text_is_normalized=True)


def extract_skills_with_fallback(text, skills_dictionary=None, *, text_is_normalized=False):
    """Return skill keys using deterministic dictionary and regex alias matching."""
    normalized_text = text if text_is_normalized else normalize_text(text)
    dictionary = SKILLS_DICTIONARY if skills_dictionary is None else skills_dictionary

    extracted_skills = {
        skill
        for skill, aliases in dictionary.items()
        if any(_contains_alias(normalized_text, alias) for alias in aliases)
    }
    return sorted(extracted_skills)


def extract_skill_labels(text, skills_dictionary=None):
    """Return display labels for extracted skills without changing key output."""
    return get_skill_display_labels(extract_skills(text, skills_dictionary))


def get_skill_display_label(skill):
    """Return the canonical display label for an internal skill key or alias."""
    skill_key = normalize_skill_key(skill)
    return SKILL_DISPLAY_LABELS.get(skill_key, _title_skill_label(skill_key))


def get_skill_display_labels(skills):
    """Return canonical display labels for an iterable of internal skill keys."""
    return [get_skill_display_label(skill) for skill in skills]


def normalize_skill_key(skill, skills_dictionary=None):
    """Normalize a skill name or alias to the stable internal dictionary key."""
    normalized_skill = normalize_text(skill)
    dictionary = SKILLS_DICTIONARY if skills_dictionary is None else skills_dictionary
    for skill_key, aliases in dictionary.items():
        normalized_key = normalize_text(skill_key)
        normalized_aliases = {normalize_text(alias) for alias in aliases}
        if normalized_skill == normalized_key or normalized_skill in normalized_aliases:
            return skill_key
    return normalized_skill


def _extract_skills_with_spacy(normalized_text, dictionary):
    nlp = _load_spacy_model()
    if nlp is None:
        return None

    try:
        matcher = _build_phrase_matcher(nlp, dictionary)
        doc = nlp(normalized_text)
        matches = matcher(doc)
    except Exception:
        return None

    extracted_skills = set()
    for match_id, _start, _end in matches:
        skill_key = _match_id_to_skill_key(nlp, match_id)
        if skill_key in dictionary:
            extracted_skills.add(skill_key)
    return extracted_skills


@lru_cache(maxsize=1)
def _load_spacy_model():
    if importlib.util.find_spec('spacy') is None:
        return None

    spacy = importlib.import_module('spacy')
    try:
        return spacy.load(SPACY_MODEL_NAME)
    except OSError:
        return None


def _build_phrase_matcher(nlp, dictionary):
    phrase_matcher_class = _get_phrase_matcher_class()
    matcher = phrase_matcher_class(nlp.vocab, attr='LOWER')
    for skill_key, aliases in dictionary.items():
        patterns = [nlp.make_doc(normalize_text(alias)) for alias in aliases]
        matcher.add(skill_key, patterns)
    return matcher


def _get_phrase_matcher_class():
    matcher_module = importlib.import_module('spacy.matcher')
    return matcher_module.PhraseMatcher


def _match_id_to_skill_key(nlp, match_id):
    try:
        return nlp.vocab.strings[match_id]
    except (KeyError, TypeError):
        return str(match_id)


def _contains_alias(normalized_text, alias):
    normalized_alias = normalize_text(alias)
    pattern = rf'(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])'
    return bool(re.search(pattern, normalized_text))


def _title_skill_label(skill_key):
    return ' '.join(part.capitalize() for part in skill_key.split())
