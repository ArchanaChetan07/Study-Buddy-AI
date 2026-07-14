<div align="center">

<img src="https://img.shields.io/badge/Study%20Buddy%20AI-v2.1-7F77DD?style=for-the-badge&logo=openai&logoColor=white" alt="Study Buddy AI"/>

# 🧠 Study Buddy AI

**An adaptive quiz agent built on Groq LLaMA 3.1**  
*Plan a quiz, generate questions, check quality, revise if needed, and optionally follow up on weak areas.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)](https://langchain.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.1-F55036?style=flat-square&logo=meta&logoColor=white)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![CI](https://img.shields.io/badge/CI-pytest%20%2B%20ruff-2088FF?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/ArchanaChetan07/Study-Buddy-AI/actions)

<br/>

</div>

---

## What is Study Buddy AI?

Study Buddy AI is a **single adaptive tutoring agent** (not a multi-agent AGI system). It turns any topic into a structured quiz, validates question quality, revises bad generations, scores your answers, and can plan a short remedial follow-up from missed items.

```
Topic → plan quiz → generate questions (tool) → observe quality (count/format)
      → revise if invalid → take quiz → score → optional adaptive follow-up
```

Live generation uses **Groq LLaMA 3.1**. With `DEMO_MODE=1` (or a missing API key), deterministic stubs run offline — no Groq calls.

---

## Features

| Feature | Description |
|---|---|
| **Adaptive quiz agent** | Plan → generate → observe → revise loop with tracing |
| **Quality checks** | Expected question count + MCQ/fill-blank format validation |
| **Adaptive follow-up** | After scoring, optional remedial questions from weak areas |
| **Two question types** | Multiple Choice (MCQ) and Fill in the Blank |
| **Three difficulty levels** | Easy · Medium · Hard |
| **Detailed results** | Per-question breakdown with correct answers |
| **Session history** | Sidebar tracks your last 5 quiz sessions |
| **CSV export** | Download results with timestamps |
| **DEMO_MODE** | Offline stubs for local tests / CI without Groq |
| **Docker / K8s** | Multi-stage image and sample manifests |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Study Buddy AI                            │
│                                                                  │
│  Streamlit UI ──▶ QuizManager ──▶ Tutoring agent loop            │
│                                      │                           │
│                 plan → generate_quiz_questions (tool)            │
│                      → observe_quiz_quality (count/format)       │
│                      → revise_invalid_questions (if needed)      │
│                      → (after score) identify_weak_areas         │
│                      → generate_adaptive_followup                │
│                                      │                           │
│                 QuestionGenerator ──▶ Groq LLaMA  / DEMO stubs   │
│                 + Trace spans (JSON-friendly)                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Project structure

```
study-buddy-ai/
├── application.py                 # Streamlit entry point (quiz UI)
├── requirements.txt
├── tests/
│   ├── conftest.py                # Forces DEMO_MODE for offline pytest
│   ├── test_study_buddy.py
│   └── test_agent_loop.py
└── src/
    ├── agent/                     # Tutoring loop (plan/observe/revise)
    │   ├── loop.py
    │   ├── planner.py
    │   ├── tools.py
    │   └── types.py
    ├── tracing.py                 # Lightweight run spans
    ├── generator/question_generator.py
    ├── llm/groq_client.py
    ├── models/question_schemas.py
    ├── prompts/templates.py
    ├── config/settings.py
    └── utils/helpers.py           # QuizManager
```

---

## Quick start

### Prerequisites

- Python 3.11+
- A free [Groq API key](https://console.groq.com/keys) (optional if using `DEMO_MODE=1`)

### Setup

```bash
git clone https://github.com/ArchanaChetan07/Study-Buddy-AI.git
cd Study-Buddy-AI
cp .env.example .env   # add GROQ_API_KEY, or set DEMO_MODE=1
pip install -e .
pip install pytest
```

### Run the app

```bash
streamlit run application.py
```

Open [http://localhost:8501](http://localhost:8501).

### Offline / demo

```bash
set DEMO_MODE=1          # Windows
export DEMO_MODE=1       # macOS / Linux
streamlit run application.py
```

### Tests

```bash
DEMO_MODE=1 pytest tests/ -v
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(empty)* | Groq API key (required for live generation) |
| `DEMO_MODE` | auto if key missing | `1` forces stub questions (no Groq) |
| `MODEL_NAME` | `llama-3.1-8b-instant` | Groq model |
| `TEMPERATURE` | `0.85` | Creativity |
| `MAX_RETRIES` | `3` | Per-question LLM parse retries |
| `MAX_AGENT_STEPS` | `8` | Cap on plan/revise tool steps |

---

## How the tutoring agent works

1. **Plan** — schedule generate + quality observe steps  
2. **Generate** — `generate_quiz_questions` tool (LLM or DEMO stubs)  
3. **Observe** — count must match; MCQ needs 4 options with answer ∈ options; fill-blank needs `___`  
4. **Revise** — regenerate once/twice if quality fails  
5. **Score** — existing quiz UI evaluates answers  
6. **Adaptive follow-up** (optional) — if misses exist, identify weak areas and generate a short remedial set  

This is a **focused quiz tutoring loop**, not an open-ended multi-agent AGI.

---

## Docker

```bash
docker build -t study-buddy-ai .
docker run -p 8501:8501 -e DEMO_MODE=1 study-buddy-ai
# or live: -e GROQ_API_KEY=your_key_here
```

---

## Contributing

1. Fork and branch: `git checkout -b feat/your-feature`
2. Keep `DEMO_MODE=1 pytest tests/ -v` and `ruff check . --select E,W,F --ignore E501` green
3. Open a PR against `main`
