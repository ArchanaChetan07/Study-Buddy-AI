"""Plan → generate → observe → revise tutoring loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.agent.planner import (
    create_adaptive_followup_plan,
    create_initial_plan,
    revise_plan,
)
from src.agent.tools import call_tool
from src.agent.types import AgentState, Observation, Plan
from src.config.settings import settings
from src.tracing import Trace, new_run_id, span


@dataclass
class AgentResult:
    state: AgentState
    trace: Trace
    status: str
    message: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


def _apply_observation(state: AgentState, obs: Observation) -> None:
    state.observations.append(obs)
    if not obs.ok:
        return

    if obs.tool in {"generate_quiz_questions", "revise_invalid_questions"}:
        state.questions = list(obs.data or [])
        state.generation_attempted = True
    elif obs.tool == "observe_quiz_quality":
        quality = obs.data or {}
        state.quality_ok = bool(quality.get("ok"))
        state.quality_issues = list(quality.get("issues") or [])
        obs.quality = quality
    elif obs.tool == "identify_weak_areas":
        state.weak_areas = list(obs.data or [])
    elif obs.tool == "generate_adaptive_followup":
        state.follow_up_questions = list(obs.data or [])


def _tool_args_for_step(state: AgentState, step_tool: str, args: dict[str, Any]) -> dict[str, Any]:
    """Keep observe/follow-up args in sync with latest state."""
    out = dict(args)
    if step_tool == "observe_quiz_quality":
        out["questions"] = state.questions
        out.setdefault("expected_count", state.num_questions)
        out.setdefault("question_type", state.question_type)
    elif step_tool == "generate_adaptive_followup":
        out["weak_areas"] = state.weak_areas
        out.setdefault("topic", state.topic)
        out.setdefault("question_type", state.question_type)
        out.setdefault("base_difficulty", state.difficulty)
    elif step_tool == "identify_weak_areas":
        out["results"] = state.results
        out.setdefault("topic", state.topic)
    return out


def _execute_plan(state: AgentState, plan: Plan, trace: Trace) -> None:
    for step in plan.steps:
        with span(trace, f"tool:{step.tool}", reason=step.reason) as s:
            try:
                args = _tool_args_for_step(state, step.tool, step.args)
                result = call_tool(step.tool, **args)
                obs = Observation(tool=step.tool, ok=True, data=result)
                s.attrs["ok"] = True
                if step.tool == "observe_quiz_quality" and isinstance(result, dict):
                    s.attrs["quality_ok"] = bool(result.get("ok"))
                    s.attrs["issue_count"] = len(result.get("issues") or [])
            except Exception as e:
                obs = Observation(tool=step.tool, ok=False, error=str(e))
                s.attrs["ok"] = False
                s.status = "error"
                s.error = str(e)
            _apply_observation(state, obs)


def run_quiz_generation_loop(
    topic: str,
    *,
    question_type: str = "Multiple Choice",
    difficulty: str = "Medium",
    num_questions: int = 5,
) -> AgentResult:
    """
    Tutoring generation loop:
      plan quiz → generate questions → observe quality → revise if invalid.
    """
    state = AgentState(
        topic=topic.strip(),
        question_type=question_type,
        difficulty=difficulty,
        num_questions=max(1, int(num_questions)),
    )
    trace = Trace(run_id=new_run_id())
    steps_used = 0
    max_steps = settings.MAX_AGENT_STEPS

    with span(trace, "phase:generate", topic=state.topic):
        plan = create_initial_plan(state)
        _execute_plan(state, plan, trace)
        steps_used += len(plan.steps)

        while not state.quality_ok and steps_used < max_steps:
            plan = revise_plan(state)
            if plan is None:
                break
            _execute_plan(state, plan, trace)
            steps_used += len(plan.steps)

    if state.quality_ok and state.questions:
        status = "ok"
        message = f"Generated {len(state.questions)} valid questions."
    elif state.questions:
        status = "partial"
        message = "Questions generated but quality checks still failing."
    else:
        status = "error"
        message = "Failed to generate questions."

    return AgentResult(
        state=state,
        trace=trace,
        status=status,
        message=message,
        extras={
            "revisions": state.revisions,
            "quality_issues": list(state.quality_issues),
        },
    )


def run_adaptive_followup(
    state: AgentState,
    *,
    results: list[dict[str, Any]] | None = None,
    previous_trace: Trace | None = None,
) -> AgentResult:
    """
    After scoring: optionally plan remedial follow-up questions from weak areas.
    Pass quiz evaluation results (with is_correct) to drive adaptation.
    """
    if results is not None:
        state.results = list(results)

    trace = previous_trace or Trace(run_id=new_run_id())
    plan = create_adaptive_followup_plan(state)
    state.follow_up_plan = plan

    with span(trace, "phase:adaptive_followup"):
        if plan is None:
            return AgentResult(
                state=state,
                trace=trace,
                status="skipped",
                message="No weak areas — follow-up not needed.",
            )
        _execute_plan(state, plan, trace)

    status = "ok" if state.follow_up_questions else "empty"
    return AgentResult(
        state=state,
        trace=trace,
        status=status,
        message=(
            f"Adaptive follow-up ready ({len(state.follow_up_questions)} questions)."
            if state.follow_up_questions
            else "Weak areas found but no follow-up questions produced."
        ),
        extras={"weak_areas": list(state.weak_areas)},
    )
