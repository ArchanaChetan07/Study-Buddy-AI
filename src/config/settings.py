"""
settings.py — Application-wide configuration.

All values can be overridden via environment variables or a .env file.
"""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # ── LLM ───────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    # Best open-source model available on Groq for instruction following.
    # Swap to "llama-3.3-70b-versatile" for higher quality at the cost of speed.
    MODEL_NAME: str = "llama-3.1-8b-instant"

    # Higher temperature → more creative / varied questions.
    # Keep in 0.7–1.0 for good question diversity.
    TEMPERATURE: float = 0.85

    # ── Retry logic ───────────────────────────────────────────────────────────
    MAX_RETRIES: int = 3

    # ── Quiz defaults (used as fallback if UI is unavailable) ─────────────────
    DEFAULT_NUM_QUESTIONS: int = 5
    DEFAULT_DIFFICULTY: str = "medium"
    DEFAULT_QUESTION_TYPE: str = "Multiple Choice"

    def validate(self) -> None:
        """Raise if required settings are missing."""
        if not self.GROQ_API_KEY:
            raise EnvironmentError(
                "GROQ_API_KEY is missing. "
                "Create a .env file with GROQ_API_KEY=<your-key>."
            )


settings = Settings()
