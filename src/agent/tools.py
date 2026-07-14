"""Tools for the adaptive quiz tutoring agent."""

from __future__ import annotations

from typing import Any, Callable

from src.generator.question_generator import QuestionGenerator


ToolFn = Callable[..., Any]


def _question_to_dict(q: Any, question_type: str) -> dict[str, Any]:
    if question_type == "Multiple Choice":
        return {
            "type": "MCQ",
            "question": q.question,
            "options": list(q.options),
            "correct_answer": q.correct_answer,
        }
    return {
        "type": "Fill in the blank",
        "question": q.question,
        "options": [],
        "correct_answer": q.answer,
    }


def generate_quiz_questions(
    topic: str,
    question_type: str = "Multiple Choice",
    difficulty: str = "Medium",
    num_questions: int = 5,
    *,
    generator: QuestionGenerator | None = None,
) -> list[dict[str, Any]]:
    """Generate a batch of quiz questions (LLM or DEMO_MODE stubs)."""
    gen = generator or QuestionGenerator()
    difficulty_key = (difficulty or "medium").lower()
    questions: list[dict[str, Any]] = []

    for _ in range(max(1, int(num_questions))):
        if question_type == "Multiple Choice":
            q = gen.generate_mcq(topic, difficulty_key)
        else:
            q = gen.generate_fill_blank(topic, difficulty_key)
        questions.append(_question_to_dict(q, question_type))

    return questions


def observe_quiz_quality(
    questions: list[dict[str, Any]],
    expected_count: int,
    question_type: str = "Multiple Choice",
) -> dict[str, Any]:
    """
    Observe generated quiz quality: expected count + per-question format checks.
    Returns {ok, issues, valid_count, expected_count}.
    """
    issues: list[str] = []
    expected = max(1, int(expected_count))

    if not isinstance(questions, list):
        return {
            "ok": False,
            "issues": ["questions is not a list"],
            "valid_count": 0,
            "expected_count": expected,
        }

    if len(questions) != expected:
        issues.append(f"expected {expected} questions, got {len(questions)}")

    valid_count = 0
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            issues.append(f"Q{i + 1}: not a dict")
            continue
        text = (q.get("question") or "").strip()
        if not text:
            issues.append(f"Q{i + 1}: empty question text")
            continue

        qtype = q.get("type") or (
            "MCQ" if question_type == "Multiple Choice" else "Fill in the blank"
        )

        if qtype == "MCQ" or question_type == "Multiple Choice":
            options = q.get("options") or []
            correct = (q.get("correct_answer") or "").strip()
            if len(options) != 4:
                issues.append(f"Q{i + 1}: MCQ must have exactly 4 options, got {len(options)}")
                continue
            if not correct:
                issues.append(f"Q{i + 1}: missing correct_answer")
                continue
            if correct not in options:
                issues.append(f"Q{i + 1}: correct_answer not in options")
                continue
        else:
            answer = (q.get("correct_answer") or q.get("answer") or "").strip()
            if "___" not in text:
                issues.append(f"Q{i + 1}: fill-blank must contain '___'")
                continue
            if not answer:
                issues.append(f"Q{i + 1}: empty fill-blank answer")
                continue

        valid_count += 1

    ok = len(issues) == 0 and valid_count == expected
    return {
        "ok": ok,
        "issues": issues,
        "valid_count": valid_count,
        "expected_count": expected,
    }


def revise_invalid_questions(
    topic: str,
    question_type: str,
    difficulty: str,
    num_questions: int,
    previous_issues: list[str] | None = None,
    *,
    generator: QuestionGenerator | None = None,
) -> list[dict[str, Any]]:
    """
    Regenerate the quiz after a failed quality observation.
    Uses a slightly adjusted difficulty hint when format issues suggest over-complexity.
    """
    _ = previous_issues  # available for richer revise policies later
    # Nudge toward medium if hard generation produced bad structure
    revised_difficulty = difficulty
    if (difficulty or "").lower() == "hard":
        revised_difficulty = "Medium"
    return generate_quiz_questions(
        topic=topic,
        question_type=question_type,
        difficulty=revised_difficulty,
        num_questions=num_questions,
        generator=generator,
    )


def identify_weak_areas(results: list[dict[str, Any]], topic: str) -> list[str]:
    """Derive simple weak-area tags from incorrect answers."""
    if not results:
        return []
    wrong = [r for r in results if not r.get("is_correct")]
    if not wrong:
        return []

    areas: list[str] = []
    # Topic-level gap when many misses
    miss_rate = len(wrong) / max(1, len(results))
    if miss_rate >= 0.5:
        areas.append(f"{topic} fundamentals")
    else:
        areas.append(f"{topic} (missed items)")

    for r in wrong[:3]:
        qtext = (r.get("question") or "").strip()
        if qtext:
            # Short snippet as a focus hint
            snippet = qtext[:60].rstrip("….")
            areas.append(f"Review: {snippet}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for a in areas:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique


def generate_adaptive_followup(
    topic: str,
    weak_areas: list[str],
    question_type: str = "Multiple Choice",
    base_difficulty: str = "Medium",
    num_questions: int = 3,
    *,
    generator: QuestionGenerator | None = None,
) -> list[dict[str, Any]]:
    """Generate a short follow-up quiz focused on weak areas (easier difficulty)."""
    if not weak_areas:
        return []

    # Drop difficulty one step to reinforce gaps
    level = (base_difficulty or "Medium").lower()
    follow_diff = {"hard": "Medium", "medium": "Easy", "easy": "Easy"}.get(level, "Easy")
    focus = weak_areas[0]
    follow_topic = f"{topic} — focus: {focus}"
    return generate_quiz_questions(
        topic=follow_topic,
        question_type=question_type,
        difficulty=follow_diff,
        num_questions=num_questions,
        generator=generator,
    )


TOOLS: dict[str, ToolFn] = {
    "generate_quiz_questions": generate_quiz_questions,
    "observe_quiz_quality": observe_quiz_quality,
    "revise_invalid_questions": revise_invalid_questions,
    "identify_weak_areas": identify_weak_areas,
    "generate_adaptive_followup": generate_adaptive_followup,
}


def call_tool(name: str, **kwargs: Any) -> Any:
    if name not in TOOLS:
        raise KeyError(f"Unknown tool: {name}")
    return TOOLS[name](**kwargs)
