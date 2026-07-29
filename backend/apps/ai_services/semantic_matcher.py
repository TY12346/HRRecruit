"""Sentence-BERT similarity and conservative, human-readable resume evidence."""

from functools import lru_cache
import re

from django.conf import settings

from .resume_preprocessor import preprocess_for_semantic_matching


DEFAULT_MODEL_NAME = 'all-MiniLM-L6-v2'
MAX_RESUME_PASSAGES = 100
MAX_JOB_PASSAGES = 30
MAX_PASSAGE_LENGTH = 360
SEMANTIC_EVIDENCE_THRESHOLD = 65.0
LEXICAL_EVIDENCE_THRESHOLD = 0.5
LOW_LEXICAL_OVERLAP = 0.3
SECOND_EVIDENCE_DISTINCTNESS = 0.6
_STOP_WORDS = frozenset('a an and are as at be by for from in is it of on or the this to with you your required preferred minimum'.split())
_SECTION_HEADINGS = {
    'education': ('education', 'academic background', 'qualifications'),
    'certification': ('certifications', 'certification', 'licenses', 'licences', 'training', 'courses'),
    'experience': ('experience', 'work experience', 'employment', 'professional experience', 'career history'),
    'projects': ('projects', 'project experience', 'portfolio'),
    'skills': ('skills', 'technical skills', 'competencies', 'technologies', 'expertise'),
    'volunteering': ('volunteering', 'volunteer experience', 'community involvement'),
    'contact_header': ('contact', 'personal details', 'profile'),
}
_COMPATIBLE_SECTIONS = {
    'education': {'education'},
    'certification': {'certification'},
    'experience': {'experience', 'projects'},
    'skill': {'skills', 'experience', 'projects'},
    'other': {'experience', 'projects', 'volunteering'},
}


def semantic_similarity(resume_text, job_description):
    """Return a 0-100 similarity, with a clearly lexical non-AI fallback."""
    left = preprocess_for_semantic_matching(resume_text)
    right = preprocess_for_semantic_matching(job_description)
    if not left or not right:
        return 0.0
    if not getattr(settings, 'AI_USE_SENTENCE_BERT', False):
        return _fallback_similarity(left, right)
    try:
        return _sentence_bert_similarity(left, right)
    except (ImportError, OSError, RuntimeError, TypeError, AttributeError, IndexError):
        return _fallback_similarity(left, right)


def split_passages(text, limit=MAX_RESUME_PASSAGES):
    """Split resume text into concise, section-aware passages preserving display text."""
    lines = str(text or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    passages, seen, section = [], set(), 'contact_header'
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        heading = _heading_section(line)
        if heading:
            section = heading
            continue
        for candidate in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])|\s+[•‣▪]\s+|\s+[-–—]\s+(?=[A-Z])', line):
            display = re.sub(r'^\s*(?:[-*•‣▪]|\d+[.)])\s*', '', candidate).strip()
            display = re.sub(r'\s+', ' ', display)[:MAX_PASSAGE_LENGTH]
            normalized = preprocess_for_semantic_matching(display)
            inferred_section = _infer_section(display, section)
            if (len(display) < 8 or not normalized or normalized in seen
                    or _is_excluded(display, inferred_section)):
                continue
            seen.add(normalized)
            passages.append({'text': display, 'normalized_text': normalized, 'section': inferred_section})
            if len(passages) >= limit:
                return passages
    return passages


def build_semantic_analysis(resume_text, job_title, job_description, requirements):
    """Group requirements and return only evidence that passes explicit reliability rules."""
    resume_passages = split_passages(resume_text)
    job_units = _group_requirements(requirements)
    full_job_text = ' '.join(filter(None, [job_title, job_description, *(u['text'] for u in job_units)]))
    overall = semantic_similarity(resume_text, full_job_text)
    if not job_units:
        return _analysis_payload(overall, [])

    scores = _pair_scores(job_units, resume_passages)
    results = []
    for unit_index, unit in enumerate(job_units):
        compatible = _COMPATIBLE_SECTIONS.get(unit['requirement_type'], _COMPATIBLE_SECTIONS['other'])
        candidates = []
        rejected_reasons = set()
        for passage_index, passage in enumerate(resume_passages):
            if passage['section'] not in compatible:
                rejected_reasons.add('incompatible_resume_section')
                continue
            shared, overlap, exact = _lexical_evidence(unit['text'], passage['text'])
            semantic_score = scores[unit_index][passage_index] if scores else None
            match_type, reason = _classify_match(exact, overlap, semantic_score)
            if match_type == 'insufficient_evidence':
                rejected_reasons.add(reason)
                continue
            candidates.append((semantic_score, overlap, passage, match_type, exact, shared))
        candidates.sort(key=lambda item: (item[3] == 'direct_phrase_match', item[1], item[0] or 0), reverse=True)
        selected = []
        for candidate in candidates:
            if selected and not _materially_different(candidate[2]['normalized_text'], selected[0][2]['normalized_text']):
                continue
            selected.append(candidate)
            if len(selected) == 2:
                break
        if selected:
            for rank, (semantic_score, overlap, passage, match_type, exact, shared) in enumerate(selected, 1):
                results.append(_evidence_payload(unit, passage, rank, match_type, exact, overlap, shared, semantic_score, True, None))
        else:
            reason = 'no_compatible_resume_section' if not any(p['section'] in compatible for p in resume_passages) else (
                sorted(rejected_reasons)[0] if rejected_reasons else 'no_candidate_passed_relevance_checks')
            results.append(_evidence_payload(unit, None, 1, 'insufficient_evidence', False, 0, [], None, False, reason))
    return _analysis_payload(overall, results)


def _group_requirements(requirements):
    grouped = {}
    for requirement in requirements or []:
        text = getattr(requirement, 'description', None) or (requirement.get('description') if isinstance(requirement, dict) else '')
        kind = getattr(requirement, 'requirement_type', None) or (requirement.get('requirement_type') if isinstance(requirement, dict) else 'other')
        normalized = preprocess_for_semantic_matching(text)
        key = (str(kind or 'other').lower(), normalized)
        if normalized and key not in grouped:
            grouped[key] = {'text': str(text).strip(), 'normalized_text': normalized,
                            'requirement_type': key[0], 'requirement_source': 'configured_requirement'}
    return list(grouped.values())[:MAX_JOB_PASSAGES]


def _pair_scores(units, passages):
    if not units or not passages or not getattr(settings, 'AI_USE_SENTENCE_BERT', False):
        return None
    try:
        texts = [u['normalized_text'] for u in units] + [p['normalized_text'] for p in passages]
        vectors = _get_model().encode(texts, convert_to_tensor=True, normalize_embeddings=True)
        matrix = vectors[:len(units)] @ vectors[len(units):].T
        return [[_normalize_score(float(matrix[i][j])) for j in range(len(passages))] for i in range(len(units))]
    except (ImportError, OSError, RuntimeError, TypeError, AttributeError, IndexError):
        return None


def _classify_match(exact, overlap, semantic_score):
    if exact:
        return 'direct_phrase_match', None
    if overlap >= LEXICAL_EVIDENCE_THRESHOLD:
        return 'lexical_match', None
    if semantic_score is not None and semantic_score >= SEMANTIC_EVIDENCE_THRESHOLD and overlap < LOW_LEXICAL_OVERLAP:
        return 'semantic_paraphrase', None
    if semantic_score is None:
        return 'insufficient_evidence', 'semantic_model_unavailable_and_lexical_evidence_too_weak'
    return 'insufficient_evidence', 'semantic_similarity_below_reliable_threshold'


def _evidence_payload(unit, passage, rank, match_type, exact, overlap, shared, semantic_score, reliable, reason):
    return {
        'requirement_type': unit['requirement_type'], 'requirement_text': unit['text'],
        'requirement_source': unit['requirement_source'],
        'resume_evidence': passage['text'] if passage else 'No reliable resume evidence found',
        'match_type': match_type, 'exact_phrase_match': exact,
        'lexical_overlap_score': round(overlap * 100, 2), 'shared_terms': shared,
        'semantic_similarity_score': semantic_score, 'similarity_score': semantic_score,
        'evidence_section': passage['section'] if passage else None,
        'reliable_evidence': reliable, 'suppression_reason': reason, 'rank': rank,
        'different_wording': match_type == 'semantic_paraphrase',
    }


def _lexical_evidence(requirement, evidence):
    def terms(value):
        return {t for t in re.findall(r'[a-z0-9+#.]+', value.lower()) if len(t) > 1 and t not in _STOP_WORDS}
    left, right = terms(requirement), terms(evidence)
    shared = sorted(left & right)
    overlap = len(shared) / max(1, len(left))
    left_text = preprocess_for_semantic_matching(requirement)
    right_text = preprocess_for_semantic_matching(evidence)
    exact = bool(left_text and (left_text in right_text or right_text in left_text) and len(left) >= 2)
    return shared, overlap, exact


def _materially_different(left, right):
    left_terms, right_terms = set(left.split()), set(right.split())
    return len(left_terms & right_terms) / max(1, min(len(left_terms), len(right_terms))) < SECOND_EVIDENCE_DISTINCTNESS


def _heading_section(line):
    normalized = re.sub(r'[^a-z ]', '', line.lower()).strip()
    if len(normalized.split()) > 4:
        return None
    for section, headings in _SECTION_HEADINGS.items():
        if normalized in headings:
            return section
    return None


def _infer_section(text, current):
    lowered = text.lower()
    if current != 'contact_header':
        return current
    if re.search(r'\b(university|college|bachelor|master|degree|diploma|gpa)\b', lowered): return 'education'
    if re.search(r'\b(certified|certification|certificate|licensed|training)\b', lowered): return 'certification'
    if re.search(r'\b(project|built|developed|implemented)\b', lowered): return 'projects'
    if re.search(r'\b(experience|worked|managed|engineer|developer|analyst)\b', lowered): return 'experience'
    return current


def _is_excluded(text, section):
    lowered = text.lower()
    if re.search(r'powered\s+by|curriculum vitae|resume template|page \d+ of \d+|all rights reserved', lowered):
        return True
    if section == 'contact_header':
        return True
    return bool(re.fullmatch(r'(?:https?://|www\.)\S+|\S+@\S+|[+()\d .-]{7,}', text.strip(), re.I))


def _analysis_payload(overall_score, evidence_pairs):
    return {
        'engine': 'sentence-transformers', 'model_name': DEFAULT_MODEL_NAME,
        'algorithm': 'Sentence-BERT embeddings with calibrated evidence gating; lexical matches are labelled separately',
        'overall_score': overall_score, 'comparison_source': 'job title, description, and configured requirements',
        'evidence_pairs': evidence_pairs,
        'different_wording_match_count': sum(p['match_type'] == 'semantic_paraphrase' for p in evidence_pairs),
        'limitations': ['Semantic similarity indicates contextual relatedness, not verified competence.',
                        'Evidence is suppressed when its section or relevance is uncertain.',
                        'The result requires recruiter review.'],
    }


def _fallback_similarity(left, right):
    left_terms, right_terms = set(left.split()), set(right.split())
    return round(100 * len(left_terms & right_terms) / max(1, min(len(left_terms), len(right_terms))), 2)


def _sentence_bert_similarity(left, right):
    vectors = _get_model().encode([left, right], convert_to_tensor=True, normalize_embeddings=True)
    return _normalize_score(float((vectors[0] @ vectors[1]).item()))


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(DEFAULT_MODEL_NAME)


def _normalize_score(score):
    return round(max(0.0, min(100.0, float(score) * 100)), 2)


def _validate_score(score, name):
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise TypeError(f'{name} must be a number.')
    if not 0 <= score <= 100:
        raise ValueError(f'{name} must be between 0 and 100.')
