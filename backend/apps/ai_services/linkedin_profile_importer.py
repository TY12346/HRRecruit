"""Deterministic LinkedIn profile PDF parsing helpers."""

import re

from .resume_preprocessor import normalize_whitespace
from .skill_extractor import extract_skill_labels

SECTION_NAMES = (
    "about", "summary", "activity", "experience", "education",
    "licenses", "certifications", "licenses & certifications",
    "licenses and certifications", "skills", "top skills", "recommendations",
)
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
DATE_RE = re.compile(
    rf"^({'|'.join(MONTHS)})\s+\d{{4}}\s+-\s+(Present|(?:{'|'.join(MONTHS)})\s+\d{{4}})\s*\(([^)]+)\)$",
    re.IGNORECASE,
)
EDU_DATE_RE = re.compile(rf"\(({'|'.join(MONTHS)})\s+\d{{4}}\s+-\s+({'|'.join(MONTHS)})\s+\d{{4}}\)", re.IGNORECASE)


def build_linkedin_profile_import(text):
    """Extract applicant profile fields from LinkedIn PDF text without network calls."""
    lines = _prepare_lines(text)
    sections = _split_sections(lines)
    header_lines = _header_lines(lines)

    full_name = _extract_name(header_lines)
    headline = _extract_headline(header_lines, full_name)
    location = _extract_location(header_lines, full_name, headline)
    linkedin_url = _extract_linkedin_url(lines)
    skills = _extract_sidebar_list(sections, "top skills") or _extract_skills(lines)
    certifications = _extract_sidebar_list(sections, "certifications") or _extract_sidebar_list(sections, "licenses & certifications")
    summary = _extract_paragraph_section(sections, ("summary", "about"))
    experience = _extract_experience(sections.get("experience", []))
    education = _extract_education(sections.get("education", []))

    return {
        "name": full_name,
        "full_name": full_name,
        "headline": headline,
        "location": location,
        "linkedin_url": linkedin_url,
        "summary": summary or _build_summary(headline, skills, experience, education, certifications),
        "skills": skills,
        "certifications": certifications,
        "experience": experience,
        "education": education,
        "extracted_text": text,
    }


def _prepare_lines(text):
    prepared = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or re.match(r"^Page\s+\d+\s+of\s+\d+$", line, re.IGNORECASE):
            continue
        prepared.append(line)
    return prepared


def _canonical_section(line):
    lowered = line.strip().lower()
    aliases = {"licenses and certifications": "certifications", "licenses & certifications": "certifications"}
    return aliases.get(lowered, lowered) if lowered in SECTION_NAMES else ""


def _split_sections(lines):
    sections = {}
    current = "header"
    sections[current] = []
    for line in lines:
        section = _canonical_section(line)
        if section:
            current = section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _header_lines(lines):
    for index, line in enumerate(lines):
        if line.lower() in {"summary", "about"}:
            return [candidate for candidate in lines[max(0, index - 4):index] if candidate.lower() not in {"contact", "(linkedin)"}]
    result = []
    for line in lines:
        if _canonical_section(line):
            break
        if line.lower() not in {"contact", "(linkedin)"} and not line.lower().startswith("www.linkedin.com"):
            result.append(line)
    return result


def _extract_name(lines):
    for line in lines[:12]:
        if _looks_like_location(line):
            continue
        if re.search(r"[A-Za-z]", line) and not any(token in line for token in ("|", "•")) and len(line) <= 80:
            return line
    return ""


def _extract_headline(lines, name):
    try:
        start = lines.index(name) + 1
    except ValueError:
        start = 0
    parts = []
    for line in lines[start:]:
        if _looks_like_location(line):
            break
        parts.append(line)
    return normalize_whitespace(" ".join(parts))


def _extract_location(lines, name, headline):
    for line in lines:
        if line != name and line not in headline and _looks_like_location(line):
            return line
    return ""


def _looks_like_location(line):
    return bool(re.search(r"\b(United States|Malaysia|Singapore|Canada|Kingdom|Australia)\b", line))


def _extract_linkedin_url(lines):
    for line in lines:
        match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-/%]+", line, re.IGNORECASE)
        if match:
            return match.group(0).rstrip("/")
    return ""


def _extract_sidebar_list(sections, name):
    values = []
    section_lines = sections.get(name, [])
    for index, line in enumerate(section_lines):
        if (
            line.lower() in {"summary", "about"}
            or _looks_like_location(line)
            or any(token in line for token in ("|", "•"))
            or (index + 1 < len(section_lines) and any(token in section_lines[index + 1] for token in ("|", "•")))
        ):
            break
        if 2 <= len(line) <= 140 and not DATE_RE.match(line):
            values.append(line)
    return values[:20]


def _extract_skills(lines):
    return extract_skill_labels(normalize_whitespace(" ".join(lines)))


def _extract_paragraph_section(sections, names):
    for name in names:
        if name in sections:
            return _join_wrapped_text(sections[name])
    return ""


def _extract_experience(lines):
    entries = []
    current_company = ""
    inherited_location = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if DATE_RE.match(line):
            job_title = lines[i - 1] if i > 0 else ""
            company = current_company or (lines[i - 2] if i > 1 else "")
            date_match = DATE_RE.match(line)
            entry = {
                "company_name": company,
                "job_title": job_title,
                "employment_type": "",
                "start_date": date_match.group(1).title() + " " + re.search(r"\d{4}", line).group(0),
                "end_date": date_match.group(2),
                "duration": date_match.group(3),
                "location": "",
                "description": "",
            }
            i += 1
            if i < len(lines) and _looks_like_location(lines[i]):
                entry["location"] = lines[i]
                inherited_location = lines[i]
                i += 1
            elif inherited_location and company == current_company:
                entry["location"] = inherited_location
            desc = []
            while i < len(lines) and not DATE_RE.match(lines[i]):
                if _is_company_duration(lines[i]):
                    current_company = lines[i - 1] if i > 0 else current_company
                    break
                if i + 1 < len(lines) and _is_company_duration(lines[i + 1]):
                    current_company = lines[i]
                    break
                if i + 1 < len(lines) and DATE_RE.match(lines[i + 1]):
                    break
                if i + 2 < len(lines) and DATE_RE.match(lines[i + 2]) and re.match(r"^[A-Z].*", lines[i]):
                    current_company = lines[i]
                    break
                desc.append(lines[i])
                i += 1
            entry["description"] = _join_wrapped_text(desc)
            entries.append(entry)
            continue
        if _is_company_duration(line):
            current_company = lines[i - 1] if i > 0 else current_company
            inherited_location = ""
        elif i + 2 < len(lines) and DATE_RE.match(lines[i + 2]):
            current_company = line
            inherited_location = ""
        i += 1
    return entries


def _is_company_duration(line):
    return bool(re.match(r"^\d+\s+years?(?:\s+\d+\s+months?)?$|^\d+\s+months?$", line))


def _extract_education(lines):
    merged_lines = []
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and "(" in lines[i] and ")" not in lines[i]:
            merged_lines.append(lines[i] + " " + lines[i + 1])
            i += 2
        else:
            merged_lines.append(lines[i])
            i += 1
    lines = merged_lines
    educations = []
    i = 0
    while i < len(lines):
        school = lines[i]
        detail = lines[i + 1] if i + 1 < len(lines) else ""
        date_match = EDU_DATE_RE.search(detail)
        clean_detail = EDU_DATE_RE.sub("", detail).strip(" ·")
        degree, field = (clean_detail.split(",", 1) + [""])[:2] if clean_detail else ("", "")
        educations.append({
            "school_name": school,
            "degree_name": degree.strip(),
            "field_of_study": field.strip(" ·"),
            "start_date": date_match.group(1).title() + " " + re.search(r"\d{4}", date_match.group(0)).group(0) if date_match else "",
            "end_date": date_match.group(2).title() + " " + re.findall(r"\d{4}", date_match.group(0))[-1] if date_match else "",
            "grade": "",
        })
        i += 2
    return educations


def _join_wrapped_text(lines):
    bullets = []
    current = []
    for line in lines:
        is_bullet = bool(re.match(r"^[•\-]\s*", line))
        cleaned = re.sub(r"^[•\-]\s*", "", line).strip()
        if not cleaned:
            continue
        if is_bullet and current:
            bullets.append(normalize_whitespace(" ".join(current)).rstrip("."))
            current = [cleaned]
        else:
            current.append(cleaned)
    if current:
        final_text = normalize_whitespace(" ".join(current))
        bullets.append(final_text.rstrip(".") if bullets else final_text)
    return ". ".join(bullets) + ("." if len(bullets) > 1 else "") if bullets else ""


def _build_summary(headline, skills, experience, education, certifications):
    parts = []
    if headline:
        parts.append(headline)
    if skills:
        parts.append("Skills: " + ", ".join(skills[:12]))
    if experience:
        parts.append("Experience: " + ", ".join(item["job_title"] for item in experience[:5] if item.get("job_title")))
    if education:
        parts.append("Education: " + ", ".join(item["school_name"] for item in education[:3] if item.get("school_name")))
    if certifications:
        parts.append("Certifications: " + ", ".join(certifications[:5]))
    return "\n".join(parts)
