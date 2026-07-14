"""
groq_client.py — Factory for the ChatGroq LLM instance.
"""
from __future__ import annotations

from typing import Any

from src.config.settings import settings


class _DemoLLM:
    """Minimal stub that satisfies .invoke(...).content without calling Groq."""

    def invoke(self, prompt: str) -> Any:
        # QuestionGenerator should never reach here in DEMO_MODE (stubs earlier).
        class _Msg:
            content = "{}"

        return _Msg()


def get_groq_llm():
    """
    Return a configured ChatGroq LLM instance, or a demo stub when DEMO_MODE.
    """
    if settings.DEMO_MODE:
        return _DemoLLM()

    if not settings.GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file or environment variables, or set DEMO_MODE=1."
        )

    from langchain_groq import ChatGroq

    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.MODEL_NAME,
        temperature=settings.TEMPERATURE,
        max_retries=2,
    )
