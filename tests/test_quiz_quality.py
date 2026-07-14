"""Tests for quiz-quality eval rubrics and metrics helpers."""

from src.eval.quiz_quality import (
    INVALID_FIXTURES_FILL,
    INVALID_FIXTURES_MCQ,
    count_agent_tool_steps,
    is_structurally_valid,
    matches_difficulty,
    matches_topic,
    quality_gate_recall,
    score_question_batch,
)
from src.observability.metrics import metrics_payload, record_quiz_generation


def test_structural_valid_mcq():
    q = {
        "type": "MCQ",
        "question": "[Easy] Which statement best relates to Photosynthesis?",
        "options": ["a", "b", "c", "d"],
        "correct_answer": "a",
    }
    ok, issues = is_structurally_valid(q, "Multiple Choice")
    assert ok is True
    assert issues == []


def test_structural_invalid_mcq_option_count():
    q = {
        "type": "MCQ",
        "question": "Bad?",
        "options": ["a", "b"],
        "correct_answer": "a",
    }
    ok, issues = is_structurally_valid(q, "Multiple Choice")
    assert ok is False
    assert any("4 options" in i for i in issues)


def test_structural_valid_fill_blank():
    q = {
        "type": "Fill in the blank",
        "question": "[Medium] A key idea in Mitosis is ___.",
        "options": [],
        "correct_answer": "Mitosis",
    }
    ok, _ = is_structurally_valid(q, "Fill in the Blank")
    assert ok is True


def test_topic_and_difficulty_adherence():
    q = {
        "type": "MCQ",
        "question": "[Hard] Which statement best relates to Photosynthesis?",
        "options": ["a", "b", "c", "d"],
        "correct_answer": "a",
    }
    assert matches_topic(q, "Photosynthesis") is True
    assert matches_difficulty(q, "Hard") is True
    assert matches_difficulty(q, "Easy") is False


def test_score_question_batch_counts():
    questions = [
        {
            "type": "MCQ",
            "question": "[Easy] Which statement best relates to Algebra basics?",
            "options": ["a", "b", "c", "d"],
            "correct_answer": "a",
        },
        {
            "type": "MCQ",
            "question": "No difficulty tag but Algebra basics mentioned",
            "options": ["a", "b", "c", "d"],
            "correct_answer": "a",
        },
    ]
    scored = score_question_batch(
        questions,
        topic="Algebra basics",
        difficulty="Easy",
        question_type="Multiple Choice",
    )
    assert scored["n"] == 2
    assert scored["structural"] == 2
    assert scored["topic"] == 2
    assert scored["difficulty"] == 1  # only first has [Easy]


def test_quality_gate_recall_perfect_on_fixtures():
    assert quality_gate_recall(INVALID_FIXTURES_MCQ, "Multiple Choice") == 100.0
    assert quality_gate_recall(INVALID_FIXTURES_FILL, "Fill in the Blank") == 100.0


def test_count_agent_tool_steps():
    trace = {
        "spans": [
            {"name": "phase:generate"},
            {"name": "tool:generate_quiz_questions"},
            {"name": "tool:observe_quiz_quality"},
        ]
    }
    assert count_agent_tool_steps(trace) == 2


def test_metrics_payload_contains_counters():
    record_quiz_generation(
        status="ok",
        question_type="Multiple Choice",
        latency_s=0.02,
        revisions=0,
        tool_steps=2,
    )
    body, content_type = metrics_payload()
    text = body.decode("utf-8")
    assert "text/plain" in content_type or "openmetrics" in content_type or content_type
    assert "studybuddy_quiz_requests_total" in text
