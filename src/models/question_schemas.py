"""
question_schemas.py — Pydantic models for LLM-generated question objects.
"""
from typing import List

from pydantic import BaseModel, Field, field_validator


class MCQQuestion(BaseModel):
    """Schema for a multiple-choice question with exactly 4 options."""

    question: str = Field(description="The question text")
    options: List[str] = Field(description="Exactly 4 answer options")
    correct_answer: str = Field(description="The correct answer, must match one option exactly")

    @field_validator("question", mode="before")
    @classmethod
    def coerce_question(cls, v):
        """Accept dict-valued 'question' fields from some model outputs."""
        if isinstance(v, dict):
            return v.get("description", str(v))
        return str(v)

    @field_validator("options", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            # Attempt to split comma-separated options
            return [o.strip() for o in v.split(",")]
        return v

    @field_validator("correct_answer", mode="before")
    @classmethod
    def coerce_answer(cls, v):
        if isinstance(v, dict):
            return v.get("description", str(v))
        return str(v).strip()


class FillBlankQuestion(BaseModel):
    """Schema for a fill-in-the-blank question containing '___' as the blank marker."""

    question: str = Field(
        description="Sentence with '___' as the blank placeholder"
    )
    answer: str = Field(description="The correct word or phrase for the blank")

    @field_validator("question", mode="before")
    @classmethod
    def coerce_question(cls, v):
        if isinstance(v, dict):
            return v.get("description", str(v))
        return str(v)

    @field_validator("answer", mode="before")
    @classmethod
    def coerce_answer(cls, v):
        if isinstance(v, dict):
            return v.get("description", str(v))
        return str(v).strip()
