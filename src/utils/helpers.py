"""
helpers.py — QuizManager and UI utilities.
"""
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from src.agent.loop import run_adaptive_followup, run_quiz_generation_loop
from src.generator.question_generator import QuestionGenerator


def rerun() -> None:
    """Trigger a Streamlit rerun by toggling a boolean in session state."""
    st.session_state["rerun_trigger"] = not st.session_state.get("rerun_trigger", False)


class QuizManager:
    """
    Manages the full lifecycle of a quiz:
      generate → attempt → evaluate → export
    Optional adaptive follow-up after scoring.
    """

    def __init__(self):
        self.questions: list[dict] = []
        self.user_answers: list[Optional[str]] = []
        self.results: list[dict] = []
        self.last_trace: Optional[dict] = None
        self.agent_message: str = ""
        self.follow_up_questions: list[dict] = []
        self.weak_areas: list[str] = []

    # ── Generation ────────────────────────────────────────────────────────────

    def generate_questions(
        self,
        generator: QuestionGenerator,
        topic: str,
        question_type: str,
        difficulty: str,
        num_questions: int,
        *,
        use_agent: bool = True,
    ) -> bool:
        """
        Generate questions via the tutoring agent loop (plan→generate→observe→revise)
        or fall back to direct QuestionGenerator calls when use_agent=False.
        """
        self.questions = []
        self.user_answers = []
        self.results = []
        self.follow_up_questions = []
        self.weak_areas = []
        self.last_trace = None
        self.agent_message = ""

        try:
            if use_agent:
                result = run_quiz_generation_loop(
                    topic,
                    question_type=question_type,
                    difficulty=difficulty,
                    num_questions=num_questions,
                )
                self.last_trace = result.trace.to_dict()
                self.agent_message = result.message
                if not result.state.questions:
                    st.error(result.message or "Agent failed to generate questions.")
                    return False
                self.questions = list(result.state.questions)
                self.user_answers = [None] * len(self.questions)
                return result.status in {"ok", "partial"}

            # Legacy direct path (kept for compatibility / tests)
            _ = generator  # caller may still pass a generator
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
                self.user_answers.append(None)

        except Exception as exc:
            st.error(f"Error generating questions: {exc}")
            return False

        return True

    def build_adaptive_followup(self, topic: str, question_type: str, difficulty: str):
        """After evaluate_quiz, plan remedial questions from weak areas."""
        if not self.results:
            return
        from src.agent.types import AgentState

        state = AgentState(
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            num_questions=len(self.questions),
            questions=list(self.questions),
            results=list(self.results),
        )
        result = run_adaptive_followup(state, results=self.results)
        self.weak_areas = list(result.state.weak_areas)
        self.follow_up_questions = list(result.state.follow_up_questions)
        if result.trace:
            prev = self.last_trace or {"run_id": result.trace.run_id, "spans": []}
            # Merge follow-up spans into last trace for UI
            prev_spans = list(prev.get("spans") or [])
            merged = result.trace.to_dict()
            self.last_trace = {
                "run_id": merged["run_id"],
                "spans": prev_spans + list(merged.get("spans") or []),
            }

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
