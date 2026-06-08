"""Deterministic local AI-assisted resume screening helpers."""

import re

from apps.jobs.models import JobRequirement

from .resume_preprocessor import preprocess_for_matching
from .resume_text_extractor import extract_resume_text
from .scoring import calculate_score_breakdown
from .semantic_matcher import semantic_similarity
from .skill_extractor import extract_skills


SCREENING_THRESHOLD = 60.0
EDUCATION_LEVELS = {
    'secondary': 1,
    'diploma': 2,
    'associate': 2,
    'bachelor': 3,
    'master': 4,
    'doctorate': 5,
}
EDUCATION_ALIASES = {
    'doctorate': ('doctorate', 'doctoral', 'phd', 'ph.d'),
    'master': ('master', "master's", 'msc', 'm.sc', 'mba'),
    'bachelor': ('bachelor', "bachelor's", 'degree', 'bsc', 'b.sc'),
    'associate': ('associate degree',),
    'diploma': ('diploma',),
    'secondary': ('secondary school', 'high school',),
}
YEARS_PATTERN = re.compile(r'(?P<years>\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)', re.IGNORECASE)


def build_resume_screening(application):
    """Extract a local resume and return the complete screening result."""
    resume_file = application.applicant.applicant_profile.resume_file
    resume_text = extract_resume_text(resume_file.path)
    requirements = list(application.job.requirements.all())
    comparison_text = _build_job_comparison_text(application.job, requirements)

    matching_resume_text = preprocess_for_matching(resume_text)
    matching_comparison_text = preprocess_for_matching(comparison_text)
    skill_requirements_text = preprocess_for_matching(
        _requirements_text(requirements, JobRequirement.RequirementType.SKILL)
    )
    experience_requirements_text = preprocess_for_matching(
        _requirements_text(requirements, JobRequirement.RequirementType.EXPERIENCE)
    )
    education_requirements_text = preprocess_for_matching(
        _requirements_text(requirements, JobRequirement.RequirementType.EDUCATION)
    )

    extracted_skills = extract_skills(matching_resume_text)
    required_skills = extract_skills(skill_requirements_text)
    if not required_skills:
        required_skills = extract_skills(matching_comparison_text)

    extracted_experience = extract_experience(matching_resume_text)
    required_experience = extract_experience(experience_requirements_text)
    extracted_education = extract_education(matching_resume_text)
    required_education = extract_education(education_requirements_text)

    semantic_score = semantic_similarity(matching_resume_text, matching_comparison_text)
    skill_score = calculate_skill_score(extracted_skills, required_skills)
    experience_score = calculate_experience_score(extracted_experience, required_experience)
    education_score = calculate_education_score(extracted_education, required_education)
    scores = calculate_score_breakdown(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
    )

    matched_skills = sorted(set(extracted_skills) & set(required_skills))
    missing_skills = sorted(set(required_skills) - set(extracted_skills))
    explanation = {
        'formula': '0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score',
        'threshold': SCREENING_THRESHOLD,
        'semantic': {
            'score': scores['semantic_score'],
            'comparison_source': 'job title, description, and configured requirements',
        },
        'skills': {
            'score': scores['skill_score'],
            'required': required_skills,
            'matched': matched_skills,
            'missing': missing_skills,
        },
        'experience': {
            'score': scores['experience_score'],
            'extracted_years': extracted_experience['years'],
            'required_years': required_experience['years'],
        },
        'education': {
            'score': scores['education_score'],
            'extracted_level': extracted_education['level'],
            'required_level': required_education['level'],
        },
    }
    return {
        'extracted_resume_text': resume_text,
        'extracted_skills': extracted_skills,
        'extracted_experience': extracted_experience,
        'extracted_education': extracted_education,
        **scores,
        'score_explanation': explanation,
    }


def extract_experience(text):
    """Extract the highest explicitly stated number of years from free text."""
    normalized_text = preprocess_for_matching(text)
    years = [float(match.group('years')) for match in YEARS_PATTERN.finditer(normalized_text)]
    return {'years': max(years, default=0.0)}


def extract_education(text):
    """Extract the highest education level mentioned in free text."""
    normalized_text = preprocess_for_matching(text)
    found_levels = [
        level
        for level, aliases in EDUCATION_ALIASES.items()
        if any(alias in normalized_text for alias in aliases)
    ]
    level = max(found_levels, key=EDUCATION_LEVELS.get) if found_levels else None
    return {'level': level}


def calculate_skill_score(extracted_skills, required_skills):
    """Calculate the percentage of expected dictionary skills present in a resume."""
    if not required_skills:
        return 100.0
    return round(100 * len(set(extracted_skills) & set(required_skills)) / len(set(required_skills)), 2)


def calculate_experience_score(extracted_experience, required_experience):
    """Calculate a capped score by comparing extracted and required years."""
    required_years = required_experience['years']
    if not required_years:
        return 100.0
    return round(min(100.0, 100 * extracted_experience['years'] / required_years), 2)


def calculate_education_score(extracted_education, required_education):
    """Calculate a capped score by comparing extracted and required education levels."""
    required_level = required_education['level']
    if not required_level:
        return 100.0
    extracted_level = extracted_education['level']
    if not extracted_level:
        return 0.0
    return round(min(100.0, 100 * EDUCATION_LEVELS[extracted_level] / EDUCATION_LEVELS[required_level]), 2)


def _build_job_comparison_text(job, requirements):
    return '\n'.join([job.title, job.description, *(requirement.description for requirement in requirements)])


def _requirements_text(requirements, requirement_type):
    return '\n'.join(
        requirement.description
        for requirement in requirements
        if requirement.requirement_type == requirement_type
    )
