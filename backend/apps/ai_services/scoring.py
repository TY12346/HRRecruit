"""Score calculation helpers for AI-assisted resume screening."""


SCORE_WEIGHTS = {
    'semantic_score': 0.4,
    'skill_score': 0.3,
    'experience_score': 0.2,
    'education_score': 0.1,
}


def calculate_final_score(semantic_score, skill_score, experience_score, education_score):
    """Calculate the weighted final resume-screening score on a 0-100 scale."""
    scores = {
        'semantic_score': semantic_score,
        'skill_score': skill_score,
        'experience_score': experience_score,
        'education_score': education_score,
    }
    _validate_scores(scores)
    return round(sum(scores[name] * weight for name, weight in SCORE_WEIGHTS.items()), 2)


def calculate_score_breakdown(semantic_score, skill_score, experience_score, education_score):
    """Return individual components together with their weighted final score."""
    final_score = calculate_final_score(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
    )
    return {
        'semantic_score': semantic_score,
        'skill_score': skill_score,
        'experience_score': experience_score,
        'education_score': education_score,
        'final_score': final_score,
    }


def _validate_scores(scores):
    for name, score in scores.items():
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise TypeError(f'{name} must be a number.')
        if not 0 <= score <= 100:
            raise ValueError(f'{name} must be between 0 and 100.')
