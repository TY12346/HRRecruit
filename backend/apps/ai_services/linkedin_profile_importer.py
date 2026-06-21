"""Deterministic LinkedIn profile PDF parsing helpers."""

import re

from .education_extractor import extract_education
from .experience_extractor import extract_experience
from .resume_preprocessor import normalize_whitespace
from .skill_extractor import extract_skill_labels

SECTION_NAMES = (
    "about",
    "activity",
    "experience",
    "education",
    "licenses",
    "certifications",
    "skills",
    "recommendations",
)


def build_linkedin_profile_import(text):
    """Extract applicant profile fields from LinkedIn PDF text."""
    cleaned_text = normalize_whitespace(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = _extract_name(lines)
    headline = _extract_headline(lines, name)
    skills = extract_skill_labels(cleaned_text)
    experience = extract_experience(cleaned_text)
    education = extract_education(cleaned_text)
    certifications = _extract_certifications(lines)
    linkedin_url = _extract_linkedin_url(cleaned_text)
    summary = _build_summary(headline, skills, experience, education, certifications)

    return {
        "name": name,
        "headline": headline,
        "skills": skills,
        "experience": experience,
        "education": education,
        "certifications": certifications,
        "linkedin_url": linkedin_url,
        "summary": summary,
        "extracted_text": text,
    }


def _extract_name(lines):
    ignored_prefixes = ("linkedin", "contact", "www.", "https://")
    for line in lines[:12]:
        normalized = line.lower()
        if normalized in SECTION_NAMES or normalized.startswith(ignored_prefixes):
            continue
        if 2 <= len(line) <= 80 and re.search(r"[A-Za-z]", line):
            return line
    return ""


def _extract_headline(lines, name):
    skip = {name.lower(), *SECTION_NAMES, "linkedin"}
    for line in lines[:20]:
        normalized = line.lower()
        if normalized in skip or normalized.startswith(("www.", "https://")):
            continue
        if 6 <= len(line) <= 160 and re.search(r"[A-Za-z]", line):
            return line
    return ""


def _extract_certifications(lines):
    certifications = []
    capture = False
    for line in lines:
        normalized = line.lower()
        if normalized in {
            "licenses & certifications",
            "licenses and certifications",
            "certifications",
        }:
            capture = True
            continue
        if capture and normalized in SECTION_NAMES:
            break
        if capture and 3 <= len(line) <= 140:
            certifications.append(line)
    return certifications[:10]


def _extract_linkedin_url(text):
    match = re.search(
        r"https?://(?:www\.)?linkedin\.com/in/[\w\-/%]+", text, re.IGNORECASE
    )
    return match.group(0) if match else ""


def _build_summary(headline, skills, experience, education, certifications):
    parts = []
    if headline:
        parts.append(headline)
    if skills:
        parts.append("Skills: " + ", ".join(skills[:12]))
    years = experience.get("years")
    roles = experience.get("roles") or []
    if years or roles:
        experience_bits = []
        if years:
            experience_bits.append(f"{years:g} years of experience")
        if roles:
            experience_bits.append("roles: " + ", ".join(roles[:5]))
        parts.append("Experience: " + "; ".join(experience_bits))
    education_label = education.get("level_label")
    fields = education.get("fields_of_study") or []
    if education_label or fields:
        education_bits = [bit for bit in [education_label, ", ".join(fields)] if bit]
        parts.append("Education: " + " in ".join(education_bits))
    if certifications:
        parts.append("Certifications: " + ", ".join(certifications[:5]))
    return "\n".join(parts)
