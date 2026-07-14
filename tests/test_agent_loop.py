"""Adaptive quiz agent loop tests (offline / DEMO_MODE)."""

from src.agent.loop import run_adaptive_followup, run_quiz_generation_loop
from src.agent.planner import create_adaptive_followup_plan, revise_plan
from src.agent.tools import identify_weak_areas, observe_quiz_quality
from src.agent.types import AgentState
from src.config.settings import settings
from src.generator.question_generator import QuestionGenerator


def test_demo_mode_enabled():
    assert settings.DEMO_MODE is True


def test_demo_mcq_stub():
    gen = QuestionGenerator()
    q = gen.generate_mcq("Photosynthesis", "easy")
    assert len(q.options) == 4
    assert q.correct_answer in q.options
    assert "Photosynthesis" in q.question


def test_demo_fill_blank_stub():
    gen = QuestionGenerator()
    q = gen.generate_fill_blank("Mitosis", "medium")
    assert "___" in q.question
    assert q.answer.strip()


def test_generation_loop_produces_valid_quiz():
    result = run_quiz_generation_loop(
        "Python basics",
        question_type="Multiple Choice",
        difficulty="Medium",
        num_questions=3,
    )
    assert result.status == "ok"
    assert len(result.state.questions) == 3
    assert result.state.quality_ok is True
    assert result.trace.spans
    assert any(s.name.startswith("tool:generate_quiz_questions") for s in result.trace.spans)
    assert any(s.name.startswith("tool:observe_quiz_quality") for s in result.trace.spans)


def test_observe_quality_rejects_bad_count():
    report = observe_quiz_quality(
        [{"type": "MCQ", "question": "Q?", "options": ["a", "b", "c", "d"], "correct_answer": "a"}],
        expected_count=3,
        question_type="Multiple Choice",
    )
    assert report["ok"] is False
    assert any("expected 3" in i for i in report["issues"])


def test_observe_quality_rejects_bad_format():
    report = observe_quiz_quality(
        [
            {
                "type": "MCQ",
                "question": "Bad options?",
                "options": ["only", "two"],
                "correct_answer": "only",
            }
        ],
        expected_count=1,
        question_type="Multiple Choice",
    )
    assert report["ok"] is False
    assert any("4 options" in i for i in report["issues"])


def test_revise_triggered_on_invalid_quality(monkeypatch):
    calls = {"n": 0}

    def fake_generate(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return [
                {
                    "type": "MCQ",
                    "question": "Broken?",
                    "options": ["a", "b"],
                    "correct_answer": "a",
                }
            ]
        return [
            {
                "type": "MCQ",
                "question": "Fixed question about atoms?",
                "options": ["proton", "emotion", "color", "sound"],
                "correct_answer": "proton",
            }
        ]

    from src.agent import tools as tools_mod

    monkeypatch.setitem(tools_mod.TOOLS, "generate_quiz_questions", fake_generate)
    monkeypatch.setitem(tools_mod.TOOLS, "revise_invalid_questions", fake_generate)

    result = run_quiz_generation_loop(
        "Atoms",
        question_type="Multiple Choice",
        difficulty="Hard",
        num_questions=1,
    )
    assert result.state.revisions >= 1
    assert result.state.quality_ok is True
    assert result.status == "ok"


def test_revise_plan_when_quality_bad():
    state = AgentState(
        topic="Math",
        num_questions=2,
        generation_attempted=True,
        quality_ok=False,
        quality_issues=["expected 2 questions, got 0"],
    )
    plan = revise_plan(state)
    assert plan is not None
    assert plan.notes == "phase=revise_invalid"
    assert any(s.tool == "revise_invalid_questions" for s in plan.steps)


def test_adaptive_followup_from_weak_areas():
    gen_result = run_quiz_generation_loop(
        "Cell biology",
        question_type="Multiple Choice",
        difficulty="Medium",
        num_questions=2,
    )
    state = gen_result.state
    # Simulate scoring: miss both
    state.results = [
        {
            "question_number": 1,
            "question": q["question"],
            "is_correct": False,
            "user_answer": "wrong",
            "correct_answer": q["correct_answer"],
        }
        for q in state.questions
    ]
    follow = run_adaptive_followup(state, previous_trace=gen_result.trace)
    assert follow.status == "ok"
    assert state.weak_areas
    assert state.follow_up_questions
    assert any(s.name.startswith("tool:identify_weak_areas") for s in follow.trace.spans)
    assert any(
        s.name.startswith("tool:generate_adaptive_followup") for s in follow.trace.spans
    )


def test_adaptive_followup_skipped_when_perfect():
    state = AgentState(topic="History", num_questions=1)
    state.results = [
        {
            "question_number": 1,
            "question": "When?",
            "is_correct": True,
            "user_answer": "correct",
            "correct_answer": "correct",
        }
    ]
    assert create_adaptive_followup_plan(state) is None
    follow = run_adaptive_followup(state)
    assert follow.status == "skipped"
    assert identify_weak_areas(state.results, "History") == []


def test_fill_blank_generation_loop():
    result = run_quiz_generation_loop(
        "Newton laws",
        question_type="Fill in the Blank",
        difficulty="Easy",
        num_questions=2,
    )
    assert result.status == "ok"
    assert all(q["type"] == "Fill in the blank" for q in result.state.questions)
    assert all("___" in q["question"] for q in result.state.questions)
