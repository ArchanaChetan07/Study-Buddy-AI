"""
groq_client.py — Factory for the ChatGroq LLM instance.
"""
from langchain_groq import ChatGroq

from src.config.settings import settings


def get_groq_llm() -> ChatGroq:
    """
    Return a configured ChatGroq LLM instance.
    Uses settings from src.config.settings.
    """
    if not settings.GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file or environment variables."
        )
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.MODEL_NAME,
        temperature=settings.TEMPERATURE,
        max_retries=2,
    )
