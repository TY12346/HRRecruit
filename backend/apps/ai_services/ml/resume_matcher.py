"""Trained resume/job matching helpers with deterministic fallback."""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from django.conf import settings

MODEL_VERSION = "resume-match-level3-v1"
FALLBACK_MODEL_VERSION = "resume-match-level3-fallback-v1"
ARTIFACT_FILENAME = "resume_match_model.joblib"

HYBRID_WEIGHTS = {
    "ml_suitability_score": 0.5,
    "semantic_score": 0.2,
    "skill_score": 0.15,
    "experience_score": 0.1,
    "education_score": 0.05,
}

FEATURE_NAMES = [
    "semantic_score",
    "skill_score",
    "experience_score",
    "education_score",
    "rule_based_score",
    "matched_skill_count",
    "missing_skill_count",
    "skill_coverage_ratio",
    "experience_gap_years",
    "education_gap_levels",
    "resume_word_count",
    "job_word_count",
]


def build_ml_screening_result(
    *,
    semantic_score: float,
    skill_score: float,
    experience_score: float,
    education_score: float,
    rule_based_score: float,
    matched_skills: Iterable[str] | None = None,
    missing_skills: Iterable[str] | None = None,
    experience_gap: dict[str, Any] | None = None,
    education_gap: dict[str, Any] | None = None,
    resume_text: str = "",
    job_text: str = "",
) -> dict[str, Any]:
    """Return ML-enhanced screening fields for recruiter decision support."""
    matched_skill_list = sorted({str(skill) for skill in (matched_skills or []) if skill})
    missing_skill_list = sorted({str(skill) for skill in (missing_skills or []) if skill})
    features = build_feature_vector(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        rule_based_score=rule_based_score,
        matched_skill_count=len(matched_skill_list),
        missing_skill_count=len(missing_skill_list),
        experience_gap=experience_gap or {},
        education_gap=education_gap or {},
        resume_text=resume_text,
        job_text=job_text,
    )
    prediction = _predict_with_optional_model(features)
    ml_score = _clamp_score(prediction["ml_suitability_score"])
    hybrid_score = calculate_hybrid_final_score(
        ml_suitability_score=ml_score,
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
    )
    return {
        "ml_suitability_score": ml_score,
        "ml_match_label": score_to_label(ml_score),
        "ml_confidence": prediction["ml_confidence"],
        "semantic_embedding_score": round(float(semantic_score), 2),
        "rule_based_score": round(float(rule_based_score), 2),
        "hybrid_final_score": hybrid_score,
        "top_positive_factors": build_positive_factors(
            semantic_score=semantic_score,
            skill_score=skill_score,
            experience_score=experience_score,
            education_score=education_score,
            matched_skills=matched_skill_list,
        ),
        "top_negative_factors": build_negative_factors(
            skill_score=skill_score,
            experience_score=experience_score,
            education_score=education_score,
            missing_skills=missing_skill_list,
            experience_gap=experience_gap or {},
            education_gap=education_gap or {},
        ),
        "model_version": prediction["model_version"],
        "fallback_used": prediction["fallback_used"],
        "feature_names": FEATURE_NAMES,
        "feature_values": features,
    }


def build_feature_vector(
    *,
    semantic_score: float,
    skill_score: float,
    experience_score: float,
    education_score: float,
    rule_based_score: float,
    matched_skill_count: int,
    missing_skill_count: int,
    experience_gap: dict[str, Any],
    education_gap: dict[str, Any],
    resume_text: str,
    job_text: str,
) -> list[float]:
    total_skills = matched_skill_count + missing_skill_count
    skill_coverage_ratio = matched_skill_count / total_skills if total_skills else 1.0
    return [
        _clamp_score(semantic_score),
        _clamp_score(skill_score),
        _clamp_score(experience_score),
        _clamp_score(education_score),
        _clamp_score(rule_based_score),
        float(matched_skill_count),
        float(missing_skill_count),
        round(skill_coverage_ratio, 4),
        _number(experience_gap.get("gap_years", 0.0)),
        _number(education_gap.get("gap_levels", 0.0)),
        float(len((resume_text or "").split())),
        float(len((job_text or "").split())),
    ]


def calculate_hybrid_final_score(
    *,
    ml_suitability_score: float,
    semantic_score: float,
    skill_score: float,
    experience_score: float,
    education_score: float,
) -> float:
    score = (
        HYBRID_WEIGHTS["ml_suitability_score"] * _clamp_score(ml_suitability_score)
        + HYBRID_WEIGHTS["semantic_score"] * _clamp_score(semantic_score)
        + HYBRID_WEIGHTS["skill_score"] * _clamp_score(skill_score)
        + HYBRID_WEIGHTS["experience_score"] * _clamp_score(experience_score)
        + HYBRID_WEIGHTS["education_score"] * _clamp_score(education_score)
    )
    return round(score, 2)


def score_to_label(score: float) -> str:
    score = _clamp_score(score)
    if score >= 85:
        return "strong_match"
    if score >= 65:
        return "moderate_match"
    if score >= 45:
        return "weak_match"
    return "not_suitable"


def build_positive_factors(*, semantic_score: float, skill_score: float, experience_score: float, education_score: float, matched_skills: list[str]) -> list[str]:
    factors: list[str] = []
    if matched_skills:
        factors.append(f"Matched skills: {', '.join(matched_skills[:8])}")
    if semantic_score >= 70:
        factors.append("Resume content is semantically aligned with the job description.")
    if skill_score >= 70:
        factors.append("Required skill coverage is strong.")
    if experience_score >= 70:
        factors.append("Experience level appears to satisfy the requirement.")
    if education_score >= 70:
        factors.append("Education level appears aligned with the requirement.")
    return factors[:5] or ["No major positive factor exceeded the configured threshold."]


def build_negative_factors(*, skill_score: float, experience_score: float, education_score: float, missing_skills: list[str], experience_gap: dict[str, Any], education_gap: dict[str, Any]) -> list[str]:
    factors: list[str] = []
    if missing_skills:
        factors.append(f"Missing or unclear skills: {', '.join(missing_skills[:8])}")
    if experience_score < 70 and experience_gap.get("gap_years"):
        factors.append(f"Experience gap of about {experience_gap['gap_years']} year(s).")
    elif experience_score < 70:
        factors.append("Experience evidence is weaker than the job requirement.")
    if education_score < 70 and education_gap.get("gap_levels"):
        factors.append("Education level may be below the requested level.")
    elif education_score < 70:
        factors.append("Education evidence is unclear or partially matched.")
    if skill_score < 70 and not missing_skills:
        factors.append("Skill coverage score is below the strong-match threshold.")
    return factors[:5] or ["No major negative factor exceeded the configured threshold."]


def _predict_with_optional_model(features: list[float]) -> dict[str, Any]:
    artifact = _load_artifact()
    if not artifact:
        fallback_score = features[FEATURE_NAMES.index("rule_based_score")]
        return {
            "ml_suitability_score": fallback_score,
            "ml_confidence": _fallback_confidence(fallback_score),
            "model_version": FALLBACK_MODEL_VERSION,
            "fallback_used": True,
        }
    try:
        model = artifact["model"]
        feature_names = artifact.get("feature_names", FEATURE_NAMES)
        feature_map = dict(zip(FEATURE_NAMES, features, strict=True))
        ordered_features = [feature_map[name] for name in feature_names]
        score = _clamp_score(model.predict([ordered_features])[0])
        return {
            "ml_suitability_score": score,
            "ml_confidence": _model_confidence(score, artifact),
            "model_version": artifact.get("model_version", MODEL_VERSION),
            "fallback_used": False,
        }
    except Exception:
        fallback_score = features[FEATURE_NAMES.index("rule_based_score")]
        return {
            "ml_suitability_score": fallback_score,
            "ml_confidence": _fallback_confidence(fallback_score),
            "model_version": FALLBACK_MODEL_VERSION,
            "fallback_used": True,
        }


@lru_cache(maxsize=1)
def _load_artifact() -> dict[str, Any] | None:
    artifact_path = Path(getattr(settings, "BASE_DIR", Path.cwd())) / "apps" / "ai_services" / "model_artifacts" / ARTIFACT_FILENAME
    if not artifact_path.exists():
        return None
    try:
        import joblib  # type: ignore

        return joblib.load(artifact_path)
    except Exception:
        return None


def _model_confidence(score: float, artifact: dict[str, Any]) -> float:
    metrics = artifact.get("metrics", {})
    mae = _number(metrics.get("mae", 15.0))
    base = max(0.55, 0.95 - (mae / 100.0))
    certainty = abs(score - 50.0) / 100.0
    return round(min(0.98, base + certainty), 2)


def _fallback_confidence(score: float) -> float:
    return round(min(0.85, 0.55 + abs(_clamp_score(score) - 50.0) / 140.0), 2)


def _clamp_score(value: Any) -> float:
    number = _number(value)
    if math.isnan(number) or math.isinf(number):
        return 0.0
    return round(max(0.0, min(100.0, number)), 2)


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
