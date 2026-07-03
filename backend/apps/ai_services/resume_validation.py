"""Deterministic resume content validation before resume screening."""

import re
from dataclasses import dataclass

from .resume_preprocessor import normalize_whitespace
from .skill_extractor import extract_skills

MIN_RESUME_TEXT_LENGTH = 80
EDUCATION_KEYWORDS = ('diploma', 'degree', 'bachelor', 'master', 'phd', 'doctorate', 'university', 'college', 'cgpa', 'gpa', 'computer science', 'information technology', 'accounting', 'business', 'software engineering', 'data science', 'finance', 'marketing', 'engineering')
EXPERIENCE_PATTERNS = (r'\bexperience\b', r'\bworked as\b', r'\bemployed\b', r'\bcompany\b', r'\bdeveloper\b', r'\banalyst\b', r'\bengineer\b', r'\bexecutive\b', r'\b\d+\+?\s*(years?|months?)\b')
INTERNSHIP_PATTERNS = (r'\binternship\b', r'\bintern\b', r'\bindustrial training\b')
PROJECT_KEYWORDS = ('project', 'developed', 'built', 'implemented', 'designed', 'created', 'system', 'application', 'website', 'mobile app', 'api', 'dashboard')
VALIDATION_MESSAGE = 'Please upload a resume that includes skills, education, and work experience, internship, or project details.'


@dataclass
class ResumeContentValidationError(Exception):
    """Raised when resume text is unavailable or incomplete for screening."""
    validation_result: dict

    def __str__(self):
        return self.validation_result.get('message', VALIDATION_MESSAGE)


def validate_resume_text(resume_text):
    """Return a structured deterministic validation result for extracted resume text."""
    cleaned_text = normalize_whitespace(resume_text or '')
    detected_skills = extract_skills(cleaned_text) if cleaned_text else []
    detected_fields = {
        'skills': detected_skills,
        'education': _contains_any_keyword(cleaned_text, EDUCATION_KEYWORDS),
        'experience': _contains_any_pattern(cleaned_text, EXPERIENCE_PATTERNS),
        'internship': _contains_any_pattern(cleaned_text, INTERNSHIP_PATTERNS),
        'projects': _contains_any_keyword(cleaned_text, PROJECT_KEYWORDS),
    }
    missing_fields = []
    warnings = []
    extraction_failure = False
    if len(cleaned_text) < MIN_RESUME_TEXT_LENGTH:
        extraction_failure = True
        warnings.append('Resume text could not be extracted or is too short for screening.')
    if not detected_fields['skills']:
        missing_fields.append('skills')
    if not detected_fields['education']:
        missing_fields.append('education')
    if not (detected_fields['experience'] or detected_fields['internship'] or detected_fields['projects']):
        missing_fields.append('experience_or_projects')
        warnings.append('Experience, internship, or project section is weak or unclear.')
    is_valid = not extraction_failure and not missing_fields
    return {'is_valid': is_valid, 'missing_fields': missing_fields, 'warnings': warnings, 'detected_fields': detected_fields, 'message': 'Resume content is valid for AI-assisted screening.' if is_valid else VALIDATION_MESSAGE}


def ensure_resume_text_is_valid_for_screening(resume_text):
    result = validate_resume_text(resume_text)
    if not result['is_valid']:
        raise ResumeContentValidationError(result)
    return result


def _contains_any_keyword(text, keywords):
    normalized = text.lower()
    return any(re.search(rf'(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])', normalized) for keyword in keywords)


def _contains_any_pattern(text, patterns):
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)
