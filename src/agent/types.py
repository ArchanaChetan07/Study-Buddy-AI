"""Typed structures for the adaptive quiz tutoring agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanStep:
    tool: str
    args: dict[str, Any]
    reason: str = ""


@dataclass
class Plan:
    steps: list[PlanStep]
    notes: str = ""


@dataclass
class Observation:
    tool: str
    ok: bool
    data: Any = None
    error: str | None = None
    quality: dict[str, Any] | None = None


@dataclass
class AgentState:
    topic: str
    question_type: str = "Multiple Choice"
    difficulty: str = "Medium"
    num_questions: int = 5
    questions: list[dict[str, Any]] = field(default_factory=list)
    quality_ok: bool = False
    quality_issues: list[str] = field(default_factory=list)
    generation_attempted: bool = False
    revisions: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)
    weak_areas: list[str] = field(default_factory=list)
    follow_up_questions: list[dict[str, Any]] = field(default_factory=list)
    follow_up_plan: Plan | None = None
    observations: list[Observation] = field(default_factory=list)
