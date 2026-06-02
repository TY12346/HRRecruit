"""Simple dictionary-based skill extraction for resume screening."""

import re


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
    'python': ('python',),
    'react': ('react', 'react.js', 'reactjs'),
    'rest api': ('rest api', 'rest apis', 'restful api', 'restful apis'),
    'sql': ('sql',),
}


def normalize_text(text):
    """Normalize free text while retaining symbols used in common skill names."""
    normalized_text = str(text or '').lower()
    normalized_text = re.sub(r'[^a-z0-9+#.]+', ' ', normalized_text)
    return re.sub(r'\s+', ' ', normalized_text).strip()


def extract_skills(text, skills_dictionary=None):
    """Return canonical skill names found in text using known aliases."""
    normalized_text = normalize_text(text)
    dictionary = SKILLS_DICTIONARY if skills_dictionary is None else skills_dictionary

    extracted_skills = {
        skill
        for skill, aliases in dictionary.items()
        if any(_contains_alias(normalized_text, alias) for alias in aliases)
    }
    return sorted(extracted_skills)


def _contains_alias(normalized_text, alias):
    normalized_alias = normalize_text(alias)
    pattern = rf'(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])'
    return bool(re.search(pattern, normalized_text))
