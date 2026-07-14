"""Quiz-quality scoring — structural validity, topic/difficulty adherence, agent efficiency.

All checks are deterministic rubrics (no LLM-as-judge). DEMO_MODE and live Groq outputs
share the same validators.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from src.agent.tools import observe_quiz_quality


DIFFICULTY_ALIASES = {
    "easy": {"easy", "beginner", "basic"},
    "medium": {"medium", "intermediate", "moderate"},
    "hard": {"hard", "advanced", "difficult"},
}


def is_structurally_valid(
    question: dict[str, Any], question_type: str = "Multiple Choice"
) -> tuple[bool, list[str]]:
    """Validate one question dict against MCQ / fill-blank schema rules."""
    report = observe_quiz_quality(
        [question],
        expected_count=1,
        question_type=question_type,
    )
    return bool(report["ok"]), list(report.get("issues") or [])


def topic_tokens(topic: str) -> list[str]:
    """Meaningful topic tokens (≥3 chars) for keyword adherence."""
    parts = re.findall(r"[A-Za-z0-9]+", (topic or "").lower())
    return [p for p in parts if len(p) >= 3]


def matches_topic(question: dict[str, Any], topic: str) -> bool:
    """True if any topic token (≥3 chars) appears in the question text (or answer)."""
    tokens = topic_tokens(topic)
    if not tokens:
        return True
    hay = (
        f"{question.get('question', '')} "
        f"{question.get('correct_answer', '')} "
        f"{question.get('answer', '')}"
    ).lower()
    return any(t in hay for t in tokens)


def matches_difficulty(question: dict[str, Any], difficulty: str) -> bool:
    """True if the stated difficulty (or alias) appears in the question text.

    DEMO stubs prefix ``[Easy]`` / ``[Medium]`` / ``[Hard]``. Live LLM output may
    omit an explicit tag — then this rubric fails (reported honestly).
    """
    level = (difficulty or "medium").strip().lower()
    aliases = DIFFICULTY_ALIASES.get(level, {level})
    text = (question.get("question") or "").lower()
    if re.search(rf"\[\s*{re.escape(level)}\s*\]", text, flags=re.I):
        return True
    return any(re.search(rf"\b{re.escape(a)}\b", text) for a in aliases)


def count_agent_tool_steps(trace: dict[str, Any] | None) -> int:
    """Count plan/observe/revise tool spans (excludes phase wrappers)."""
    if not trace:
        return 0
    return sum(
        1 for s in trace.get("spans") or [] if str(s.get("name", "")).startswith("tool:")
    )


def hit_retry_ceiling(revisions: int, max_revisions: int = 2) -> bool:
    """True when the revise loop exhausted its revision budget."""
    return revisions >= max_revisions


@dataclass
class QuizQualityReport:
    n_questions: int = 0
    n_runs: int = 0
    structural_valid: int = 0
    topic_adherent: int = 0
    difficulty_adherent: int = 0
    total_tool_steps: int = 0
    runs_with_revision: int = 0
    runs_hit_retry_ceiling: int = 0
    status_ok: int = 0
    mode: str = "DEMO_MODE"
    failure_notes: list[str] = field(default_factory=list)

    @property
    def structural_validity_pct(self) -> float:
        return (
            100.0 * self.structural_valid / self.n_questions if self.n_questions else 0.0
        )

    @property
    def topic_adherence_pct(self) -> float:
        return (
            100.0 * self.topic_adherent / self.n_questions if self.n_questions else 0.0
        )

    @property
    def difficulty_adherence_pct(self) -> float:
        return (
            100.0 * self.difficulty_adherent / self.n_questions
            if self.n_questions
            else 0.0
        )

    @property
    def avg_tool_steps(self) -> float:
        return self.total_tool_steps / self.n_runs if self.n_runs else 0.0

    @property
    def revision_rate_pct(self) -> float:
        return (
            100.0 * self.runs_with_revision / self.n_runs if self.n_runs else 0.0
        )

    @property
    def retry_ceiling_rate_pct(self) -> float:
        return (
            100.0 * self.runs_hit_retry_ceiling / self.n_runs if self.n_runs else 0.0
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(
            {
                "structural_validity_pct": round(self.structural_validity_pct, 1),
                "topic_adherence_pct": round(self.topic_adherence_pct, 1),
                "difficulty_adherence_pct": round(self.difficulty_adherence_pct, 1),
                "avg_tool_steps": round(self.avg_tool_steps, 2),
                "revision_rate_pct": round(self.revision_rate_pct, 1),
                "retry_ceiling_rate_pct": round(self.retry_ceiling_rate_pct, 1),
                "max_agent_steps_budget": 8,
            }
        )
        return d


def score_question_batch(
    questions: list[dict[str, Any]],
    *,
    topic: str,
    difficulty: str,
    question_type: str,
) -> dict[str, int]:
    """Score a flat list of questions; returns counts."""
    structural = topic_ok = diff_ok = 0
    for q in questions:
        ok, _ = is_structurally_valid(q, question_type)
        if ok:
            structural += 1
        if matches_topic(q, topic):
            topic_ok += 1
        if matches_difficulty(q, difficulty):
            diff_ok += 1
    return {
        "n": len(questions),
        "structural": structural,
        "topic": topic_ok,
        "difficulty": diff_ok,
    }


def quality_gate_recall(
    invalid_fixtures: list[dict[str, Any]], question_type: str
) -> float:
    """Fraction of known-bad questions correctly rejected by observe_quiz_quality."""
    if not invalid_fixtures:
        return 0.0
    caught = 0
    for q in invalid_fixtures:
        ok, _ = is_structurally_valid(q, question_type)
        if not ok:
            caught += 1
    return 100.0 * caught / len(invalid_fixtures)


INVALID_FIXTURES_MCQ: list[dict[str, Any]] = [
    {
        "type": "MCQ",
        "question": "Broken options?",
        "options": ["a", "b"],
        "correct_answer": "a",
    },
    {
        "type": "MCQ",
        "question": "Wrong answer key?",
        "options": ["a", "b", "c", "d"],
        "correct_answer": "not-in-list",
    },
    {
        "type": "MCQ",
        "question": "",
        "options": ["a", "b", "c", "d"],
        "correct_answer": "a",
    },
    {
        "type": "MCQ",
        "question": "Missing answer?",
        "options": ["a", "b", "c", "d"],
        "correct_answer": "",
    },
]

INVALID_FIXTURES_FILL: list[dict[str, Any]] = [
    {
        "type": "Fill in the blank",
        "question": "No blank marker here.",
        "options": [],
        "correct_answer": "x",
    },
    {
        "type": "Fill in the blank",
        "question": "Blank is ___ but empty answer.",
        "options": [],
        "correct_answer": "",
    },
]
