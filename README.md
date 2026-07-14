![CI](https://github.com/ArchanaChetan07/Study-Buddy-AI/actions/workflows/ci.yml/badge.svg)

Adaptive quiz-generation agent - Groq LLaMA via LangChain, plan/observe/revise loop, K8s-deployed, Streamlit UI.

**100%** structurally valid questions across **51** generated (20 DEMO_MODE runs) - avg **2.0** agent tool steps / 8 - **0%** revision rate - **29/29** tests passing.

How to run: `docker compose up --build` (DEMO_MODE, no Groq key) -> UI `http://localhost:8501`, Prometheus `http://localhost:9090/metrics` (override host port with `METRICS_HOST_PORT` if 9090 is busy).

---

## Overview

Study Buddy AI plans a quiz, generates MCQ (4 options) or fill-in-the-blank items with Groq `llama-3.1-8b-instant` (temperature 0.85), observes schema quality, revises if needed, and can produce an adaptive follow-up from weak areas. With `DEMO_MODE=1` (or no API key), deterministic offline stubs replace Groq so CI and recruiters can run the app without credentials.

MIT licensed. Jenkinsfile is present for teams that already run Jenkins (not executed in this hardening pass - GitHub Actions is the verified CI gate).

---

## Agent Loop Design

1. **Plan** - `generate_quiz_questions` then `observe_quiz_quality`
2. **Observe** - count + format checks (MCQ = 4 options and answer in options; fill-blank requires `___` + non-empty answer)
3. **Revise** - up to **2** revise cycles (`revise_invalid_questions` then re-observe) within a **MAX_AGENT_STEPS = 8** tool-step budget
4. **LLM retries** - up to **MAX_RETRIES = 3** parse retries per question when live Groq is used

Plain language: the agent generates, checks itself, and regenerates broken items before the UI shows the quiz - not a single unchecked LLM dump.

---

## Quiz Quality Eval

**Methodology (deterministic rubrics - not LLM-as-judge):**

| Metric | Definition |
|--------|------------|
| Structural validity | % of questions passing `observe_quiz_quality` schema rules |
| Topic adherence | >=1 topic token (>=3 chars) appears in question/answer text |
| Difficulty adherence | Explicit `[Easy]`/`[Medium]`/`[Hard]` tag or whole-word difficulty alias |
| Agent efficiency | Mean tool spans (`tool:*`) per run out of budget 8; revision and retry-ceiling rates |
| Quality-gate recall | % of known-bad fixtures correctly rejected by the observer |

**Measured results** (`DEMO_MODE`, committed `artifacts/quiz_quality_metrics.json`):

| Metric | Value |
|--------|------:|
| Questions scored | **51** (20 mixed topic/type/difficulty runs) |
| Structural validity | **100%** (51/51) |
| Topic adherence | **100%** (51/51) |
| Difficulty adherence | **100%** (51/51) |
| Avg agent tool steps | **2.0** / 8 |
| Revision rate | **0%** |
| Retry-ceiling hit rate | **0%** |
| Quality-gate recall (MCQ fixtures) | **100%** (4/4) |
| Quality-gate recall (fill fixtures) | **100%** (2/2) |
| Wall time | **0.003 s** |

DEMO stubs are deterministically valid (hence the perfect structural/adherence scores). That is intentional for offline CI; live Groq can miss difficulty tags or produce answer/option mismatches - the observe/revise loop and quality-gate fixtures are there to catch those. Common live failure modes: not exactly 4 MCQ options, `correct_answer` not in `options`, fill-blank missing `___`.

Reproduce:

```bash
DEMO_MODE=1 python scripts/eval_quiz_quality.py
```

---

## Observability

Prometheus metrics server on **`:9090/metrics`** (alongside Streamlit `:8501`):

| Metric | Meaning |
|--------|---------|
| `studybuddy_quiz_requests_total` | Generations by status x question type |
| `studybuddy_quiz_latency_seconds` | End-to-end agent-loop latency |
| `studybuddy_quiz_revisions_total` | Revise-loop invocations |
| `studybuddy_quiz_errors_total` | Hard generation failures |
| `studybuddy_agent_tool_steps` | Tool steps used per run |

Streamlit health remains `GET /_stcore/health`.

---

## Deployment

Kubernetes (`manifests/`):

- **2 replicas**, RollingUpdate (`maxUnavailable: 0`)
- Requests **250m CPU / 256Mi**; limits **500m / 512Mi**
- Ports **8501** (UI) + **9090** (metrics)
- Probes on `/_stcore/health`

```bash
kubectl apply --dry-run=client -f manifests/   # validated in this session
kubectl apply -f manifests/
```

---

## How to Run

```bash
git clone https://github.com/ArchanaChetan07/Study-Buddy-AI.git
cd Study-Buddy-AI

# Preferred demo path (no Groq key)
docker compose up --build
# UI  http://localhost:8501
# Metrics http://localhost:9090/metrics

# Local
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt && pip install -e .
set DEMO_MODE=1   # Windows   /   export DEMO_MODE=1
streamlit run application.py
```

Optional live mode: set `GROQ_API_KEY` and `DEMO_MODE=0`.

---

## Tests

```bash
DEMO_MODE=1 pytest tests/ -v
# 29 passed - agent loop, DEMO stubs, quiz-quality rubrics, metrics payload
```

GitHub Actions (`.github/workflows/ci.yml`) installs the package, runs ruff + pytest + `scripts/eval_quiz_quality.py`.

Jenkins: `Jenkinsfile` exists but was **not** executed here - treat GitHub Actions as the public green gate.

---

## Tech Stack

| Layer | Tech |
|-------|------|
| UI | Streamlit |
| LLM | Groq LLaMA 3.1 8B (LangChain) · DEMO stubs offline |
| Agent | plan -> observe -> revise (max 8 steps, 3 LLM retries) |
| Schemas | Pydantic MCQ / fill-blank |
| Observability | prometheus-client `:9090` |
| Deploy | Docker Compose · Kubernetes |
| Quality | pytest · ruff · quiz-quality eval script |

---

## License

MIT - see [`LICENSE`](LICENSE).
