"""
helpers.py — QuizManager and UI utilities.
"""
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from src.generator.question_generator import QuestionGenerator


def rerun() -> None:
    """Trigger a Streamlit rerun by toggling a boolean in session state."""
    st.session_state["rerun_trigger"] = not st.session_state.get("rerun_trigger", False)


class QuizManager:
    """
    Manages the full lifecycle of a quiz:
      generate → attempt → evaluate → export
    """

    def __init__(self):
        self.questions: list[dict] = []
        self.user_answers: list[Optional[str]] = []
        self.results: list[dict] = []

    # ── Generation ────────────────────────────────────────────────────────────

    def generate_questions(
        self,
        generator: QuestionGenerator,
        topic: str,
        question_type: str,
        difficulty: str,
        num_questions: int,
    ) -> bool:
        """Call the LLM to generate questions and store them in self.questions."""
        self.questions = []
        self.user_answers = []
        self.results = []

        try:
            for _ in range(num_questions):
                if question_type == "Multiple Choice":
                    q = generator.generate_mcq(topic, difficulty.lower())
                    self.questions.append(
                        {
                            "type": "MCQ",
                            "question": q.question,
                            "options": q.options,
                            "correct_answer": q.correct_answer,
                        }
                    )
                else:
                    q = generator.generate_fill_blank(topic, difficulty.lower())
                    self.questions.append(
                        {
                            "type": "Fill in the blank",
                            "question": q.question,
                            "options": [],
                            "correct_answer": q.answer,
                        }
                    )
                # Pre-fill answers list with None placeholders
                self.user_answers.append(None)

        except Exception as exc:
            st.error(f"Error generating questions: {exc}")
            return False

        return True

    # ── Evaluation ────────────────────────────────────────────────────────────

    def evaluate_quiz(self) -> None:
        """Compare user answers to correct answers and populate self.results."""
        self.results = []

        for i, (q, user_ans) in enumerate(zip(self.questions, self.user_answers)):
            user_ans = (user_ans or "").strip()
            correct_ans = q["correct_answer"].strip()

            if q["type"] == "MCQ":
                is_correct = user_ans == correct_ans
            else:
                is_correct = user_ans.lower() == correct_ans.lower()

            self.results.append(
                {
                    "question_number": i + 1,
                    "question": q["question"],
                    "question_type": q["type"],
                    "options": q.get("options", []),
                    "user_answer": user_ans or "(no answer)",
                    "correct_answer": correct_ans,
                    "is_correct": is_correct,
                }
            )

    # ── Export ────────────────────────────────────────────────────────────────

    def generate_result_dataframe(self) -> pd.DataFrame:
        """Return results as a tidy DataFrame."""
        if not self.results:
            return pd.DataFrame()
        return pd.DataFrame(self.results)

    def save_to_csv(self, filename_prefix: str = "quiz_results") -> Optional[str]:
        """
        Persist results to CSV under results/<prefix>_<timestamp>.csv.
        Returns the saved path or None on failure.
        """
        if not self.results:
            st.warning("No results to save.")
            return None

        df = self.generate_result_dataframe()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"

        os.makedirs("results", exist_ok=True)
        filepath = os.path.join("results", filename)

        try:
            df.to_csv(filepath, index=False)
            st.success(f"Results saved to `{filepath}`.")
            return filepath
        except Exception as exc:
            st.error(f"Failed to save results: {exc}")
            return None

    # ── Summary helpers ───────────────────────────────────────────────────────

    @property
    def score_percent(self) -> float:
        """Return the percentage of correct answers (0–100)."""
        if not self.results:
            return 0.0
        correct = sum(1 for r in self.results if r["is_correct"])
        return (correct / len(self.results)) * 100

    def summary(self) -> dict:
        """Return a compact result summary dict for session history."""
        if not self.results:
            return {}
        correct = sum(1 for r in self.results if r["is_correct"])
        return {
            "total": len(self.results),
            "correct": correct,
            "score_percent": round(self.score_percent),
        }
