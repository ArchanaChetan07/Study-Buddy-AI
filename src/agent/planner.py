"""Planner and reviser for the adaptive quiz tutoring agent."""

from __future__ import annotations

from src.agent.types import AgentState, Plan, PlanStep


def create_initial_plan(state: AgentState) -> Plan:
    """Plan: generate quiz questions, then observe count/format quality."""
    return Plan(
        steps=[
            PlanStep(
                "generate_quiz_questions",
                {
                    "topic": state.topic,
                    "question_type": state.question_type,
                    "difficulty": state.difficulty,
                    "num_questions": state.num_questions,
                },
                "Generate quiz questions for the topic",
            ),
            PlanStep(
                "observe_quiz_quality",
                {
                    "expected_count": state.num_questions,
                    "question_type": state.question_type,
                },
                "Validate question count and format",
            ),
        ],
        notes="phase=generate",
    )


def revise_plan(state: AgentState) -> Plan | None:
    """
    Observe → revise:
    If quality checks failed and we have remaining revision budget,
    regenerate questions and re-observe.
    """
    if state.quality_ok:
        return None
    if state.revisions >= 2:
        return None
    if not state.generation_attempted:
        return None

    state.revisions += 1
    return Plan(
        steps=[
            PlanStep(
                "revise_invalid_questions",
                {
                    "topic": state.topic,
                    "question_type": state.question_type,
                    "difficulty": state.difficulty,
                    "num_questions": state.num_questions,
                    "previous_issues": list(state.quality_issues),
                },
                "Regenerate after failed quality checks",
            ),
            PlanStep(
                "observe_quiz_quality",
                {
                    "expected_count": state.num_questions,
                    "question_type": state.question_type,
                },
                "Re-validate after revise",
            ),
        ],
        notes="phase=revise_invalid",
    )


def create_adaptive_followup_plan(state: AgentState) -> Plan | None:
    """After scoring: if weak areas exist, plan a short remedial follow-up quiz."""
    if not state.results:
        return None
    wrong = [r for r in state.results if not r.get("is_correct")]
    if not wrong:
        return None

    follow_n = min(3, max(1, len(wrong)))
    return Plan(
        steps=[
            PlanStep(
                "identify_weak_areas",
                {"results": state.results, "topic": state.topic},
                "Identify weak areas from incorrect answers",
            ),
            PlanStep(
                "generate_adaptive_followup",
                {
                    "topic": state.topic,
                    "question_type": state.question_type,
                    "base_difficulty": state.difficulty,
                    "num_questions": follow_n,
                },
                "Generate remedial follow-up questions",
            ),
        ],
        notes="phase=adaptive_followup",
    )
