"""
question_generator.py — LLM-backed question generation with retry logic.
Supports DEMO_MODE stubs so tests and offline demos run without Groq.
"""
from __future__ import annotations

from src.common.custom_exception import CustomException
from src.common.logger import get_logger
from src.config.settings import settings
from src.llm.groq_client import get_groq_llm
from src.models.question_schemas import FillBlankQuestion, MCQQuestion


def _demo_mcq(topic: str, difficulty: str) -> MCQQuestion:
    """Deterministic offline MCQ for DEMO_MODE."""
    topic_label = (topic or "General knowledge").strip() or "General knowledge"
    level = (difficulty or "medium").capitalize()
    correct = f"A core fact about {topic_label}"
    return MCQQuestion(
        question=f"[{level}] Which statement best relates to {topic_label}?",
        options=[
            correct,
            f"An unrelated claim about {topic_label}",
            f"A common misconception about {topic_label}",
            f"A detail from a different subject than {topic_label}",
        ],
        correct_answer=correct,
    )


def _demo_fill_blank(topic: str, difficulty: str) -> FillBlankQuestion:
    """Deterministic offline fill-in-the-blank for DEMO_MODE."""
    topic_label = (topic or "General knowledge").strip() or "General knowledge"
    level = (difficulty or "medium").capitalize()
    return FillBlankQuestion(
        question=f"[{level}] A key idea in {topic_label} is ___.",
        answer=topic_label.split()[0] if topic_label.split() else "concept",
    )


class QuestionGenerator:
    """
    Generates MCQ and fill-in-the-blank questions via Groq LLaMA (or DEMO stubs).
    Includes retry logic and structural validation.
    """

    def __init__(self):
        self.llm = get_groq_llm()
        self.logger = get_logger(self.__class__.__name__)
        self.demo_mode = settings.DEMO_MODE

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _retry_and_parse(self, prompt, parser, topic: str, difficulty: str):
        """
        Invoke the LLM with the given prompt and parse the response.
        Retries up to settings.MAX_RETRIES times on failure.
        """
        last_error = None
        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                self.logger.info(
                    "Generating question | topic=%s difficulty=%s attempt=%d",
                    topic,
                    difficulty,
                    attempt,
                )
                response = self.llm.invoke(
                    prompt.format(topic=topic, difficulty=difficulty)
                )
                parsed = parser.parse(response.content)
                self.logger.info("Successfully parsed question on attempt %d", attempt)
                return parsed

            except Exception as exc:
                last_error = exc
                self.logger.warning("Attempt %d failed: %s", attempt, str(exc))

        raise CustomException(
            f"Generation failed after {settings.MAX_RETRIES} attempts",
            last_error,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_mcq(self, topic: str, difficulty: str = "medium") -> MCQQuestion:
        """
        Generate a validated multiple-choice question.

        Validation rules:
        - Exactly 4 options
        - correct_answer must be one of the options
        """
        try:
            if self.demo_mode:
                question = _demo_mcq(topic, difficulty)
            else:
                from langchain_core.output_parsers import PydanticOutputParser

                from src.prompts.templates import mcq_prompt_template

                parser = PydanticOutputParser(pydantic_object=MCQQuestion)
                question = self._retry_and_parse(
                    mcq_prompt_template, parser, topic, difficulty
                )

            # Structural validation
            if len(question.options) != 4:
                raise ValueError(
                    f"MCQ must have exactly 4 options, got {len(question.options)}"
                )
            if question.correct_answer not in question.options:
                raise ValueError(
                    f"correct_answer '{question.correct_answer}' is not in options"
                )

            self.logger.info("Valid MCQ generated for topic '%s'", topic)
            return question

        except Exception as exc:
            self.logger.error("MCQ generation failed: %s", str(exc))
            raise CustomException("MCQ generation failed", exc)

    def generate_fill_blank(
        self, topic: str, difficulty: str = "medium"
    ) -> FillBlankQuestion:
        """
        Generate a validated fill-in-the-blank question.

        Validation rules:
        - question text must contain '___'
        - answer must be non-empty
        """
        try:
            if self.demo_mode:
                question = _demo_fill_blank(topic, difficulty)
            else:
                from langchain_core.output_parsers import PydanticOutputParser

                from src.prompts.templates import fill_blank_prompt_template

                parser = PydanticOutputParser(pydantic_object=FillBlankQuestion)
                question = self._retry_and_parse(
                    fill_blank_prompt_template, parser, topic, difficulty
                )

            # Structural validation
            if "___" not in question.question:
                raise ValueError(
                    "Fill-in-the-blank question must contain '___' as a placeholder"
                )
            if not question.answer.strip():
                raise ValueError("Fill-in-the-blank answer must not be empty")

            self.logger.info(
                "Valid fill-in-the-blank question generated for topic '%s'", topic
            )
            return question

        except Exception as exc:
            self.logger.error("Fill-in-the-blank generation failed: %s", str(exc))
            raise CustomException("Fill-in-the-blank generation failed", exc)
