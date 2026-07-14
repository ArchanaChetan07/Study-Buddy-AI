"""
settings.py — Application-wide configuration.

All values can be overridden via environment variables or a .env file.
"""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # ── LLM ───────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    # Best open-source model available on Groq for instruction following.
    # Swap to "llama-3.3-70b-versatile" for higher quality at the cost of speed.
    MODEL_NAME: str = field(
        default_factory=lambda: os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
    )

    # Higher temperature → more creative / varied questions.
    # Keep in 0.7–1.0 for good question diversity.
    TEMPERATURE: float = field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.85"))
    )

    # ── Demo / offline mode ───────────────────────────────────────────────────
    # Forced when DEMO_MODE=1, or automatically when GROQ_API_KEY is missing.
    DEMO_MODE: bool = field(default=False)

    # ── Retry / agent loop ────────────────────────────────────────────────────
    MAX_RETRIES: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRIES", "3"))
    )
    MAX_AGENT_STEPS: int = field(
        default_factory=lambda: int(os.getenv("MAX_AGENT_STEPS", "8"))
    )

    # ── Quiz defaults (used as fallback if UI is unavailable) ─────────────────
    DEFAULT_NUM_QUESTIONS: int = 5
    DEFAULT_DIFFICULTY: str = "medium"
    DEFAULT_QUESTION_TYPE: str = "Multiple Choice"

    def __post_init__(self) -> None:
        # Recompute DEMO_MODE from env + key presence after fields init
        forced = _env_bool("DEMO_MODE", False)
        object.__setattr__(
            self,
            "DEMO_MODE",
            forced or not bool(self.GROQ_API_KEY.strip()),
        )

    def validate(self) -> None:
        """Raise if required settings are missing for live (non-demo) mode."""
        if self.DEMO_MODE:
            return
        if not self.GROQ_API_KEY:
            raise EnvironmentError(
                "GROQ_API_KEY is missing. "
                "Create a .env file with GROQ_API_KEY=<your-key> or set DEMO_MODE=1."
            )


settings = Settings()
