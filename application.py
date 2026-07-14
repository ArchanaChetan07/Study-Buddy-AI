"""
Study Buddy AI — Main Application
A polished Streamlit quiz app powered by Groq LLaMA.
"""
import os
import streamlit as st
from dotenv import load_dotenv
from src.utils.helpers import QuizManager, rerun
from src.generator.question_generator import QuestionGenerator

load_dotenv()


def configure_page():
    st.set_page_config(
        page_title="Study Buddy AI",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        /* ── Global reset ─────────────────────────────── */
        [data-testid="stSidebar"] { background: #F8F7FF; }
        .block-container { padding-top: 1.5rem; max-width: 860px; }

        /* ── Branding strip ───────────────────────────── */
        .brand-row {
            display: flex; align-items: center; gap: 10px;
            padding: 6px 0 20px;
        }
        .brand-icon {
            width: 38px; height: 38px; border-radius: 10px;
            background: #534AB7; display: flex; align-items: center;
            justify-content: center; font-size: 20px; color: #fff;
        }
        .brand-name { font-size: 17px; font-weight: 600; color: #1a1a2e; line-height: 1.2; }
        .brand-tag  { font-size: 12px; color: #6b6b80; }

        /* ── Question cards ───────────────────────────── */
        .q-card {
            background: #fff; border: 1px solid #E8E7F8;
            border-radius: 12px; padding: 18px 20px; margin-bottom: 14px;
        }
        .q-badge {
            display: inline-block; background: #EEEDFE; color: #534AB7;
            font-size: 11px; font-weight: 600; padding: 2px 9px;
            border-radius: 99px; margin-bottom: 10px;
        }
        .q-text { font-size: 15px; font-weight: 500; color: #1a1a2e; }

        /* ── Score bar ────────────────────────────────── */
        .score-wrap { background: #F8F7FF; border-radius: 10px; padding: 16px 18px; }
        .score-bar-track {
            height: 8px; background: #E8E7F8; border-radius: 99px;
            overflow: hidden; margin-top: 8px;
        }
        .score-bar-fill {
            height: 100%; border-radius: 99px;
            transition: width .5s cubic-bezier(.4,0,.2,1);
        }

        /* ── Result rows ──────────────────────────────── */
        .res-ok  { color: #0F6E56; }
        .res-bad { color: #993C1D; }

        /* ── Sidebar form polish ──────────────────────── */
        div[data-testid="stNumberInput"] input { border-radius: 8px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state():
    defaults = {
        "quiz_manager": QuizManager(),
        "quiz_generated": False,
        "quiz_submitted": False,
        "rerun_trigger": False,
        "active_tab": "quiz",
        "history": [],          # list of past result summaries
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def sidebar():
    """Render sidebar and return quiz settings."""
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-row">
              <div class="brand-icon">🧠</div>
              <div>
                <div class="brand-name">Study Buddy AI</div>
                <div class="brand-tag">Adaptive quiz agent</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        topic = st.text_input(
            "Topic",
            placeholder="e.g. Indian History, Python basics…",
            help="Be specific for better questions.",
        )

        question_type = st.selectbox(
            "Question type",
            ["Multiple Choice", "Fill in the Blank"],
            index=0,
        )

        difficulty = st.select_slider(
            "Difficulty",
            options=["Easy", "Medium", "Hard"],
            value="Medium",
        )

        num_questions = st.slider(
            "Number of questions",
            min_value=1,
            max_value=10,
            value=5,
        )

        st.divider()
        generate = st.button("✨ Generate quiz", use_container_width=True, type="primary")

        if st.session_state.history:
            st.caption("Past sessions")
            for h in reversed(st.session_state.history[-5:]):
                st.caption(
                    f"**{h['topic']}** · {h['score']}% · {h['correct']}/{h['total']} correct"
                )

    return topic, question_type, difficulty, num_questions, generate


def render_quiz():
    qm: QuizManager = st.session_state.quiz_manager
    total = len(qm.questions)
    answered = sum(1 for a in qm.user_answers if a is not None and a != "")
    pct = int((answered / total) * 100) if total else 0

    # Progress header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(pct / 100, text=f"{answered} of {total} answered")

    for i, q in enumerate(qm.questions):
        with st.container():
            badge = "MCQ" if q["type"] == "MCQ" else "Fill in the blank"
            st.markdown(
                f'<div class="q-card">'
                f'<span class="q-badge">{badge} · Q{i+1}</span>'
                f'<div class="q-text">{q["question"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

            if q["type"] == "MCQ":
                current = qm.user_answers[i] if i < len(qm.user_answers) else None
                idx = q["options"].index(current) if current in q["options"] else 0
                answer = st.radio(
                    "Choose an answer",
                    q["options"],
                    index=idx,
                    key=f"mcq_{i}",
                    label_visibility="collapsed",
                )
                if i < len(qm.user_answers):
                    qm.user_answers[i] = answer
            else:
                current = qm.user_answers[i] if i < len(qm.user_answers) else ""
                answer = st.text_input(
                    "Your answer",
                    value=current or "",
                    key=f"fill_{i}",
                    placeholder="Type your answer here…",
                    label_visibility="collapsed",
                )
                if i < len(qm.user_answers):
                    qm.user_answers[i] = answer

    st.divider()
    col_l, col_r = st.columns([1, 1])
    with col_l:
        if st.button("🔄 New quiz", use_container_width=True):
            st.session_state.quiz_generated = False
            st.session_state.quiz_submitted = False
            rerun()
    with col_r:
        if st.button("✅ Submit quiz", use_container_width=True, type="primary"):
            qm.evaluate_quiz()
            topic = st.session_state.get("current_topic", "Unknown")
            qtype = st.session_state.get("current_question_type", "Multiple Choice")
            diff = st.session_state.get("current_difficulty", "Medium")
            qm.build_adaptive_followup(topic, qtype, diff)
            st.session_state.quiz_submitted = True
            # Save to history
            df = qm.generate_result_dataframe()
            if not df.empty:
                correct = int(df["is_correct"].sum())
                total_q = len(df)
                score = round((correct / total_q) * 100)
                st.session_state.history.append(
                    {
                        "topic": topic,
                        "score": score,
                        "correct": correct,
                        "total": total_q,
                    }
                )
            rerun()


def render_results():
    qm: QuizManager = st.session_state.quiz_manager
    df = qm.generate_result_dataframe()

    if df.empty:
        st.warning("No results to display.")
        return

    correct = int(df["is_correct"].sum())
    total = len(df)
    score_pct = round((correct / total) * 100)

    # Score summary
    bar_color = (
        "#1D9E75" if score_pct >= 80 else "#BA7517" if score_pct >= 50 else "#D85A30"
    )
    grade = (
        "🌟 Excellent!" if score_pct >= 80
        else "📈 Good effort" if score_pct >= 50
        else "📚 Keep practising"
    )

    st.markdown(
        f"""
        <div class="score-wrap">
          <div style="display:flex;justify-content:space-between;align-items:baseline">
            <span style="font-weight:600;font-size:16px;color:#1a1a2e">{grade}</span>
            <span style="font-size:22px;font-weight:700;color:{bar_color}">{score_pct}%</span>
          </div>
          <div class="score-bar-track">
            <div class="score-bar-fill" style="width:{score_pct}%;background:{bar_color}"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Correct", f"{correct} / {total}")
    col2.metric("Score", f"{score_pct}%")
    col3.metric("Questions", str(total))

    st.divider()
    st.subheader("Question breakdown")

    for _, row in df.iterrows():
        icon = "✅" if row["is_correct"] else "❌"
        with st.expander(f"{icon} Q{row['question_number']}: {row['question'][:80]}…"):
            if row["is_correct"]:
                st.success(f"Your answer: **{row['user_answer']}**")
            else:
                st.error(f"Your answer: **{row['user_answer']}**")
                st.info(f"Correct answer: **{row['correct_answer']}**")

    if qm.weak_areas:
        st.subheader("Adaptive follow-up")
        st.caption("Based on missed answers, the agent planned a short remedial set.")
        st.write("Weak areas: " + "; ".join(qm.weak_areas[:4]))
        if qm.follow_up_questions:
            for i, fq in enumerate(qm.follow_up_questions):
                st.markdown(f"**Practice {i + 1}.** {fq.get('question', '')}")
                if fq.get("type") == "MCQ" and fq.get("options"):
                    st.caption("Options: " + " · ".join(fq["options"]))

    if qm.last_trace:
        with st.expander("Agent trace"):
            st.json(qm.last_trace)

    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("🔄 Take again", use_container_width=True):
            st.session_state.quiz_submitted = False
            rerun()
    with col_b:
        if st.button("🆕 New quiz", use_container_width=True):
            st.session_state.quiz_generated = False
            st.session_state.quiz_submitted = False
            rerun()
    with col_c:
        if st.button("💾 Save results", use_container_width=True):
            saved = qm.save_to_csv()
            if saved:
                with open(saved, "rb") as f:
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=f.read(),
                        file_name=os.path.basename(saved),
                        mime="text/csv",
                        use_container_width=True,
                    )


def main():
    configure_page()
    init_session_state()

    topic, question_type, difficulty, num_questions, generate = sidebar()

    if generate:
        if not topic.strip():
            st.error("Please enter a topic before generating a quiz.")
            return

        st.session_state.current_topic = topic
        st.session_state.current_question_type = question_type
        st.session_state.current_difficulty = difficulty
        st.session_state.quiz_submitted = False

        with st.spinner(
            f"Agent planning & generating {num_questions} {difficulty.lower()} "
            f"questions on **{topic}**…"
        ):
            generator = QuestionGenerator()
            success = st.session_state.quiz_manager.generate_questions(
                generator, topic, question_type, difficulty, num_questions
            )
            st.session_state.quiz_generated = success

        if success:
            st.toast(f"✅ {num_questions} questions ready!", icon="🎉")
        else:
            st.error(
                "Failed to generate questions. Check your API key, "
                "set DEMO_MODE=1 for offline stubs, or try a different topic."
            )

    if not st.session_state.quiz_generated:
        # Welcome state
        st.markdown("## Welcome to Study Buddy AI")
        st.markdown(
            "Select a topic in the sidebar, choose your settings, and hit **Generate quiz**. "
            "An adaptive tutoring agent plans the quiz, checks question quality, "
            "revises if needed, and can suggest a short follow-up after you score."
        )
        col1, col2, col3 = st.columns(3)
        col1.info("**📝 Multiple choice** or fill-in-the-blank questions")
        col2.info("**🎯 Easy → Hard** difficulty levels")
        col3.info("**📊 Results + adaptive follow-up** from weak areas")
        return

    topic_display = st.session_state.get("current_topic", topic)
    st.markdown(f"## {topic_display}")

    if st.session_state.quiz_submitted:
        render_results()
    else:
        render_quiz()


if __name__ == "__main__":
    main()
