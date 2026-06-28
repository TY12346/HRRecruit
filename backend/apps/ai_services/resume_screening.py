"""Deterministic local AI-assisted resume screening helpers."""

from decimal import Decimal

from apps.jobs.models import JobRequirement

from .education_extractor import EDUCATION_LEVELS, extract_education
from .experience_extractor import extract_experience
from .ml.resume_matcher import build_ml_screening_result
from .resume_preprocessor import preprocess_for_matching
from .resume_text_extractor import extract_resume_text
from .scoring import calculate_score_breakdown
from .semantic_matcher import semantic_similarity
from .skill_extractor import extract_skills


SCREENING_THRESHOLD = 60.0

def build_resume_screening(application):
    """Extract a local resume and return the complete screening result."""
    resume_file = get_application_resume_file(application)
    resume_text = extract_resume_text(resume_file.path)
    requirements = list(application.job.requirements.all())
    comparison_text = _build_job_comparison_text(application.job, requirements)

    matching_resume_text = preprocess_for_matching(resume_text)
    matching_comparison_text = preprocess_for_matching(comparison_text)
    skill_requirements = _skill_requirement_details(requirements)
    skill_requirements_text = preprocess_for_matching(
        _requirements_text(requirements, JobRequirement.RequirementType.SKILL)
    )

    extracted_skills = extract_skills(matching_resume_text)
    required_skills = sorted({skill for requirement in skill_requirements for skill in requirement['skills']})
    if not required_skills:
        required_skills = extract_skills(skill_requirements_text)
    if not required_skills:
        required_skills = extract_skills(matching_comparison_text)

    extracted_experience = extract_experience(resume_text)
    required_experience = extract_experience(
        _requirements_text(requirements, JobRequirement.RequirementType.EXPERIENCE)
    )
    extracted_education = extract_education(resume_text)
    required_education = extract_education(
        _requirements_text(requirements, JobRequirement.RequirementType.EDUCATION)
    )

    semantic_score = semantic_similarity(matching_resume_text, matching_comparison_text)
    skill_score = calculate_skill_score(extracted_skills, required_skills, skill_requirements)
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
    education_match, education_gap = describe_education_match(extracted_education, required_education)
    experience_match, experience_gap = describe_experience_match(extracted_experience, required_experience)
    notes = build_score_notes(
        matched_skills,
        missing_skills,
        education_match,
        education_gap,
        experience_match,
        experience_gap,
    )
    ml_screening = build_ml_screening_result(
        semantic_score=scores['semantic_score'],
        skill_score=scores['skill_score'],
        experience_score=scores['experience_score'],
        education_score=scores['education_score'],
        rule_based_score=scores['final_score'],
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        experience_gap={
            **experience_gap,
            'gap_years': experience_gap.get('missing_years', 0.0),
        },
        education_gap={
            **education_gap,
            'gap_levels': _education_gap_levels(extracted_education, required_education),
        },
        resume_text=matching_resume_text,
        job_text=matching_comparison_text,
    )
    formula = '0.4 * semantic_score + 0.3 * skill_score + 0.2 * experience_score + 0.1 * education_score'
    explanation = {
        'formula': formula,
        'threshold': SCREENING_THRESHOLD,
        'semantic_score': scores['semantic_score'],
        'skill_score': scores['skill_score'],
        'experience_score': scores['experience_score'],
        'education_score': scores['education_score'],
        'final_score': scores['final_score'],
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'education_match': education_match,
        'education_gap': education_gap,
        'experience_match': experience_match,
        'experience_gap': experience_gap,
        'notes': notes,
        'ml_screening': ml_screening,
        'hybrid_formula': '0.5 * ml_suitability_score + 0.2 * semantic_score + 0.15 * skill_score + 0.1 * experience_score + 0.05 * education_score',
        'semantic': {
            'score': scores['semantic_score'],
            'comparison_source': 'job title, description, and configured requirements',
        },
        'skills': {
            'score': scores['skill_score'],
            'required': required_skills,
            'matched': matched_skills,
            'missing': missing_skills,
            'weights': _skill_weights_by_key(skill_requirements, required_skills),
        },
        'experience': {
            'score': scores['experience_score'],
            'extracted_years': extracted_experience['years'],
            'required_years': required_experience['years'],
            'extracted_roles': extracted_experience.get('roles', []),
            'required_roles': required_experience.get('roles', []),
            'match': experience_match,
            'gap': experience_gap,
        },
        'education': {
            'score': scores['education_score'],
            'extracted_level': extracted_education['level'],
            'required_level': required_education['level'],
            'extracted_fields_of_study': extracted_education.get('fields_of_study', []),
            'required_fields_of_study': required_education.get('fields_of_study', []),
            'match': education_match,
            'gap': education_gap,
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


def get_application_resume_file(application):
    if getattr(application, 'resume_id', None) and application.resume and application.resume.resume_file:
        return application.resume.resume_file
    return application.applicant.applicant_profile.resume_file


def calculate_skill_score(extracted_skills, required_skills, skill_requirements=None):
    """Calculate weighted required-skill coverage on a 0-100 scale."""
    required_set = set(required_skills)
    if not required_set:
        return 100.0

    skill_weights = _skill_weights_by_key(skill_requirements or [], required_skills)
    if not skill_weights:
        skill_weights = {skill: 1.0 for skill in required_set}

    total_weight = sum(skill_weights.values())
    if total_weight <= 0:
        return round(100 * len(set(extracted_skills) & required_set) / len(required_set), 2)

    extracted_skill_set = set(extracted_skills)
    matched_weight = sum(
        weight for skill, weight in skill_weights.items() if skill in extracted_skill_set
    )
    return round(min(100.0, 100 * matched_weight / total_weight), 2)


def calculate_experience_score(extracted_experience, required_experience):
    """Calculate a capped score using required years and role signals."""
    required_years = required_experience.get('years', 0.0)
    required_roles = set(required_experience.get('roles', []))
    extracted_roles = set(extracted_experience.get('roles', []))

    year_score = (
        100.0
        if not required_years
        else min(100.0, 100 * extracted_experience.get('years', 0.0) / required_years)
    )
    if not required_roles:
        return round(year_score, 2)

    role_score = 100 * len(extracted_roles & required_roles) / len(required_roles)
    if not required_years:
        return round(role_score, 2)
    return round((0.8 * year_score) + (0.2 * role_score), 2)


def calculate_education_score(extracted_education, required_education):
    """Calculate a capped score using required level and field-of-study signals."""
    required_level = required_education.get('level')
    required_fields = set(required_education.get('fields_of_study', []))
    extracted_fields = set(extracted_education.get('fields_of_study', []))

    if required_level:
        extracted_level = extracted_education.get('level')
        level_score = (
            0.0
            if not extracted_level
            else min(100.0, 100 * EDUCATION_LEVELS[extracted_level] / EDUCATION_LEVELS[required_level])
        )
    else:
        level_score = 100.0

    if not required_fields:
        return round(level_score, 2)

    field_score = 100 * len(extracted_fields & required_fields) / len(required_fields)
    if not required_level:
        return round(field_score, 2)
    return round((0.7 * level_score) + (0.3 * field_score), 2)


def describe_experience_match(extracted_experience, required_experience):
    required_years = required_experience.get('years', 0.0)
    extracted_years = extracted_experience.get('years', 0.0)
    required_roles = set(required_experience.get('roles', []))
    extracted_roles = set(extracted_experience.get('roles', []))
    missing_roles = sorted(required_roles - extracted_roles)
    missing_years = max(0.0, round(required_years - extracted_years, 2))
    match = missing_years == 0 and not missing_roles
    gap = {
        'required_years': required_years,
        'extracted_years': extracted_years,
        'missing_years': missing_years,
        'required_roles': sorted(required_roles),
        'extracted_roles': sorted(extracted_roles),
        'missing_roles': missing_roles,
    }
    return match, gap


def _education_gap_levels(extracted_education, required_education):
    required_level = required_education.get('level')
    extracted_level = extracted_education.get('level')
    if not required_level:
        return 0
    required_rank = EDUCATION_LEVELS[required_level]
    extracted_rank = EDUCATION_LEVELS.get(extracted_level, 0)
    return max(0, required_rank - extracted_rank)


def describe_education_match(extracted_education, required_education):
    required_level = required_education.get('level')
    extracted_level = extracted_education.get('level')
    required_fields = set(required_education.get('fields_of_study', []))
    extracted_fields = set(extracted_education.get('fields_of_study', []))
    level_gap = None
    if required_level and not extracted_level:
        level_gap = f"Missing required education level: {required_education.get('level_label') or required_level}."
    elif required_level and EDUCATION_LEVELS[extracted_level] < EDUCATION_LEVELS[required_level]:
        required_label = required_education.get('level_label') or required_level
        extracted_label = extracted_education.get('level_label') or extracted_level
        level_gap = f'Requires {required_label}; candidate has {extracted_label}.'

    missing_fields = sorted(required_fields - extracted_fields)
    match = level_gap is None and not missing_fields
    gap = {
        'required_level': required_level,
        'extracted_level': extracted_level,
        'level_gap': level_gap,
        'required_fields_of_study': sorted(required_fields),
        'extracted_fields_of_study': sorted(extracted_fields),
        'missing_fields_of_study': missing_fields,
    }
    return match, gap


def build_score_notes(
    matched_skills,
    missing_skills,
    education_match,
    education_gap,
    experience_match,
    experience_gap,
):
    notes = []
    if matched_skills:
        notes.append(f"Matched required skills: {', '.join(matched_skills)}.")
    if missing_skills:
        notes.append(f"Missing required skills: {', '.join(missing_skills)}.")
    if not experience_match:
        missing_years = experience_gap.get('missing_years', 0.0)
        missing_roles = experience_gap.get('missing_roles', [])
        if missing_years:
            notes.append(f"Experience gap: {missing_years:g} year(s) below requirement.")
        if missing_roles:
            notes.append(f"Missing required experience roles: {', '.join(missing_roles)}.")
    if not education_match:
        if education_gap.get('level_gap'):
            notes.append(f"Education gap: {education_gap['level_gap']}")
        missing_fields = education_gap.get('missing_fields_of_study', [])
        if missing_fields:
            notes.append(f"Missing education field(s): {', '.join(missing_fields)}.")
    if not notes:
        notes.append('Candidate meets the configured resume-screening requirements.')
    return notes


def _skill_requirement_details(requirements):
    details = []
    for requirement in requirements:
        if requirement.requirement_type != JobRequirement.RequirementType.SKILL:
            continue
        skills = extract_skills(preprocess_for_matching(requirement.description))
        if skills:
            details.append({
                'skills': skills,
                'weight_score': float(requirement.weight_score or Decimal('0')),
            })
    return details


def _skill_weights_by_key(skill_requirements, required_skills):
    required_set = set(required_skills)
    weights = {skill: 0.0 for skill in required_set}
    for requirement in skill_requirements or []:
        requirement_skills = [skill for skill in requirement.get('skills', []) if skill in required_set]
        if not requirement_skills:
            continue
        weight = float(requirement.get('weight_score') or 0)
        per_skill_weight = weight / len(requirement_skills) if weight > 0 else 0
        for skill in requirement_skills:
            weights[skill] += per_skill_weight

    return {skill: round(weight, 2) for skill, weight in weights.items() if weight > 0}


def _build_job_comparison_text(job, requirements):
    return '\n'.join([job.title, job.description, *(requirement.description for requirement in requirements)])


def _requirements_text(requirements, requirement_type):
    return '\n'.join(
        requirement.description
        for requirement in requirements
        if requirement.requirement_type == requirement_type
    )
