"""Train the supervised resume/job suitability model from labeled data."""

from __future__ import annotations

import csv
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.ai_services.education_extractor import EDUCATION_LEVELS, extract_education
from apps.ai_services.experience_extractor import extract_experience
from apps.ai_services.ml.resume_matcher import FEATURE_NAMES, MODEL_VERSION, build_feature_vector
from apps.ai_services.scoring import calculate_score_breakdown
from apps.ai_services.semantic_matcher import semantic_similarity
from apps.ai_services.skill_extractor import extract_skills


class Command(BaseCommand):
    help = "Train the ML resume/job suitability model from HRRecruit AI training data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            default="../hrrecruit_ai_training_data.zip",
            help="Path to the training dataset directory or zip file.",
        )
        parser.add_argument(
            "--output",
            default="apps/ai_services/model_artifacts/resume_match_model.joblib",
            help="Path where the trained joblib artifact should be written.",
        )
        parser.add_argument("--test-size", type=float, default=0.2)
        parser.add_argument("--random-state", type=int, default=42)
        parser.add_argument("--estimators", type=int, default=250)

    def handle(self, *args, **options):
        try:
            import joblib  # type: ignore
            from sklearn.ensemble import RandomForestRegressor  # type: ignore
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # type: ignore
            from sklearn.model_selection import train_test_split  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on optional local packages
            raise CommandError(
                "Training requires optional ML dependencies. Install scikit-learn and joblib first."
            ) from exc

        dataset_path = Path(options["dataset"]).expanduser()
        with _prepared_dataset(dataset_path) as root:
            rows = _read_labels(root / "labels.csv")
            if len(rows) < 10:
                raise CommandError("At least 10 labeled resume/job pairs are required for training.")

            features: list[list[float]] = []
            labels: list[float] = []
            for row in rows:
                resume_text = _read_text(root / "resumes" / row["resume_file"])
                job_text = _read_text(root / "jobs" / row["job_file"])
                features.append(_features_for_pair(resume_text, job_text))
                labels.append(float(row["suitability_score"]))

        test_size = options["test_size"]
        random_state = options["random_state"]
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            labels,
            test_size=test_size,
            random_state=random_state,
        )
        model = RandomForestRegressor(
            n_estimators=options["estimators"],
            random_state=random_state,
            min_samples_leaf=2,
        )
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        metrics = {
            "mae": round(mean_absolute_error(y_test, predictions), 4),
            "rmse": round(mean_squared_error(y_test, predictions) ** 0.5, 4),
            "r2": round(r2_score(y_test, predictions), 4),
            "training_pairs": len(features),
            "test_size": test_size,
        }
        artifact = {
            "model": model,
            "feature_names": FEATURE_NAMES,
            "model_version": MODEL_VERSION,
            "metrics": metrics,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }
        output_path = Path(options["output"]).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(artifact, output_path)
        metrics_path = output_path.with_suffix(".metrics.json")
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"Saved model artifact to {output_path}"))
        self.stdout.write(self.style.SUCCESS(f"Saved metrics to {metrics_path}"))
        self.stdout.write(json.dumps(metrics, indent=2))


def _features_for_pair(resume_text: str, job_text: str) -> list[float]:
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_text))
    matched_skills = resume_skills & job_skills
    missing_skills = job_skills - resume_skills
    skill_score = round((len(matched_skills) / len(job_skills)) * 100, 2) if job_skills else 100.0

    resume_experience = extract_experience(resume_text)
    job_experience = extract_experience(job_text)
    candidate_years = float(resume_experience.get("years", 0.0) or 0.0)
    required_years = float(job_experience.get("years", 0.0) or 0.0)
    experience_score = 100.0 if required_years <= 0 else round(min(candidate_years / required_years, 1.0) * 100, 2)

    resume_education = extract_education(resume_text)
    job_education = extract_education(job_text)
    candidate_level = EDUCATION_LEVELS.get(resume_education.get("level"), 0)
    required_level = EDUCATION_LEVELS.get(job_education.get("level"), 0)
    if required_level <= 0:
        education_score = 100.0
    else:
        education_score = 100.0 if candidate_level >= required_level else round((candidate_level / required_level) * 100, 2)

    semantic_score = semantic_similarity(resume_text, job_text)
    scores = calculate_score_breakdown(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
    )
    return build_feature_vector(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        rule_based_score=scores["final_score"],
        matched_skill_count=len(matched_skills),
        missing_skill_count=len(missing_skills),
        experience_gap={"gap_years": max(required_years - candidate_years, 0.0)},
        education_gap={"gap_levels": max(required_level - candidate_level, 0)},
        resume_text=resume_text,
        job_text=job_text,
    )


def _read_labels(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise CommandError(f"Missing labels file: {path}")
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _read_text(path: Path) -> str:
    if not path.exists():
        raise CommandError(f"Missing text file referenced by labels.csv: {path}")
    return path.read_text(encoding="utf-8")


class _prepared_dataset:
    def __init__(self, dataset_path: Path):
        self.dataset_path = dataset_path
        self._tmp: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> Path:
        if self.dataset_path.is_dir():
            return _dataset_root(self.dataset_path)
        if self.dataset_path.is_file() and self.dataset_path.suffix.lower() == ".zip":
            self._tmp = tempfile.TemporaryDirectory()
            with zipfile.ZipFile(self.dataset_path) as archive:
                archive.extractall(self._tmp.name)
            return _dataset_root(Path(self._tmp.name))
        raise CommandError(f"Dataset path does not exist or is not supported: {self.dataset_path}")

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self._tmp:
            self._tmp.cleanup()


def _dataset_root(path: Path) -> Path:
    if (path / "labels.csv").exists():
        return path
    nested = path / "hrrecruit_ai_training_data"
    if (nested / "labels.csv").exists():
        return nested
    raise CommandError(f"Could not find labels.csv under {path}")
