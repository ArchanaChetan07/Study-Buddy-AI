"""Batch quiz-quality evaluation (DEMO_MODE by default)."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

# Ensure repo root imports work when run as a script
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DEMO_MODE", "1")
os.environ.setdefault("GROQ_API_KEY", "")

from src.agent.loop import run_quiz_generation_loop  # noqa: E402
from src.config.settings import settings  # noqa: E402
from src.eval.quiz_quality import (  # noqa: E402
    INVALID_FIXTURES_FILL,
    INVALID_FIXTURES_MCQ,
    QuizQualityReport,
    count_agent_tool_steps,
    hit_retry_ceiling,
    quality_gate_recall,
    score_question_batch,
)


# Diverse topics × difficulties × types
CASES: list[tuple[str, str, str, int]] = [
    ("Photosynthesis", "Multiple Choice", "Easy", 3),
    ("Photosynthesis", "Multiple Choice", "Medium", 3),
    ("Photosynthesis", "Fill in the Blank", "Hard", 2),
    ("Python lists", "Multiple Choice", "Easy", 3),
    ("Python lists", "Fill in the Blank", "Medium", 2),
    ("World War II", "Multiple Choice", "Medium", 3),
    ("World War II", "Fill in the Blank", "Easy", 2),
    ("Mitosis", "Multiple Choice", "Hard", 3),
    ("Mitosis", "Fill in the Blank", "Medium", 2),
    ("Newton laws", "Multiple Choice", "Easy", 3),
    ("Newton laws", "Fill in the Blank", "Hard", 2),
    ("Indian History", "Multiple Choice", "Medium", 3),
    ("Indian History", "Fill in the Blank", "Easy", 2),
    ("DNA replication", "Multiple Choice", "Hard", 3),
    ("DNA replication", "Fill in the Blank", "Medium", 2),
    ("Algebra basics", "Multiple Choice", "Easy", 3),
    ("Algebra basics", "Fill in the Blank", "Hard", 2),
    ("Machine learning", "Multiple Choice", "Medium", 3),
    ("Machine learning", "Fill in the Blank", "Easy", 2),
    ("Cell biology", "Multiple Choice", "Hard", 3),
]


def run_eval(cases: list[tuple[str, str, str, int]] | None = None) -> dict:
    cases = cases or CASES
    report = QuizQualityReport(mode="DEMO_MODE" if settings.DEMO_MODE else "LIVE_GROQ")
    notes: list[str] = []

    t0 = time.perf_counter()
    for topic, qtype, difficulty, n in cases:
        result = run_quiz_generation_loop(
            topic,
            question_type=qtype,
            difficulty=difficulty,
            num_questions=n,
        )
        report.n_runs += 1
        if result.status == "ok":
            report.status_ok += 1
        if result.state.revisions > 0:
            report.runs_with_revision += 1
        if hit_retry_ceiling(result.state.revisions):
            report.runs_hit_retry_ceiling += 1

        steps = count_agent_tool_steps(result.trace.to_dict())
        report.total_tool_steps += steps

        scored = score_question_batch(
            result.state.questions,
            topic=topic,
            difficulty=difficulty,
            question_type=qtype,
        )
        report.n_questions += scored["n"]
        report.structural_valid += scored["structural"]
        report.topic_adherent += scored["topic"]
        report.difficulty_adherent += scored["difficulty"]

        if scored["structural"] < scored["n"]:
            notes.append(f"{topic}/{difficulty}: structural fail {scored['structural']}/{scored['n']}")
        if scored["difficulty"] < scored["n"]:
            notes.append(
                f"{topic}/{difficulty}: difficulty tag missing "
                f"{scored['difficulty']}/{scored['n']}"
            )

    elapsed = time.perf_counter() - t0
    gate_mcq = quality_gate_recall(INVALID_FIXTURES_MCQ, "Multiple Choice")
    gate_fill = quality_gate_recall(INVALID_FIXTURES_FILL, "Fill in the Blank")

    # Common failure mode note (honest)
    if report.difficulty_adherence_pct < 100:
        notes.append(
            "Difficulty adherence <100% usually means the question text lacked an "
            "explicit Easy/Medium/Hard marker (rubric requires a visible tag/keyword)."
        )
    if report.structural_validity_pct < 100:
        notes.append(
            "Structural failures commonly include ≠4 MCQ options or correct_answer "
            "not matching an option (caught by observe_quiz_quality / revise)."
        )

    report.failure_notes = notes[:12]
    out = report.to_dict()
    out["elapsed_seconds"] = round(elapsed, 3)
    out["quality_gate_recall_mcq_pct"] = round(gate_mcq, 1)
    out["quality_gate_recall_fill_pct"] = round(gate_fill, 1)
    out["n_cases"] = len(cases)
    return out


def main() -> None:
    metrics = run_eval()
    out_dir = ROOT / "artifacts"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / "quiz_quality_metrics.json"
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
