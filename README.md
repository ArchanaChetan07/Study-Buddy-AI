<div align="center">

<img src="https://img.shields.io/badge/Study%20Buddy%20AI-v2.0-7F77DD?style=for-the-badge&logo=openai&logoColor=white" alt="Study Buddy AI"/>

# 🧠 Study Buddy AI

**An AI-powered adaptive quiz engine built on Groq LLaMA 3.1**  
*Generate, attempt, and review quizzes on any topic — in seconds.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)](https://langchain.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.1-F55036?style=flat-square&logo=meta&logoColor=white)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-deployed-326CE5?style=flat-square&logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?style=flat-square&logo=jenkins&logoColor=white)](https://jenkins.io)
[![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-EF7B4D?style=flat-square&logo=argo&logoColor=white)](https://argoproj.github.io)


<br/>

![Demo](https://img.shields.io/badge/live%20demo-▶%20try%20it-534AB7?style=for-the-badge)

</div>

---

## ✨ What is Study Buddy AI?

Study Buddy AI turns **any topic** into a structured quiz in seconds. Powered by **Groq's ultra-fast LLaMA 3.1 inference**, it generates fresh, contextually accurate questions every time — no pre-baked question banks, no repetition.

```
You pick a topic  →  LLM generates questions  →  You take the quiz  →  Instant results & breakdown
```

Built with a production-grade MLOps stack: containerised with Docker, deployed on Kubernetes via a Jenkins → ArgoCD GitOps pipeline.

---

## 🎯 Features

| Feature | Description |
|---|---|
| 🤖 **AI Question Generation** | LLaMA 3.1 8B (via Groq) generates unique questions every run |
| 📝 **Two Question Types** | Multiple Choice (MCQ) and Fill in the Blank |
| 🎚️ **Three Difficulty Levels** | Easy · Medium · Hard — adjusts prompt complexity |
| 📊 **Detailed Results** | Per-question breakdown with correct answers for wrong responses |
| 📈 **Session History** | Sidebar tracks your last 5 quiz sessions with scores |
| ⬇️ **CSV Export** | Download full results with timestamps for offline review |
| 🔁 **Retry Logic** | Up to 3 LLM retries with structural validation on each response |
| 🐳 **Docker Ready** | Multi-stage build, health checks, minimal runtime image |
| ☸️ **Kubernetes Deployed** | Rolling updates, resource limits, readiness + liveness probes |
| 🔄 **Full CI/CD** | Jenkins pipeline with lint, Trivy security scan, ArgoCD GitOps sync |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Study Buddy AI                           │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────┐ │
│  │  Streamlit   │───▶│ QuizManager  │───▶│ QuestionGenerator │ │
│  │     UI       │    │  (helpers)   │    │   (generator)     │ │
│  └──────────────┘    └──────────────┘    └────────┬──────────┘ │
│                                                   │             │
│                                          ┌────────▼──────────┐ │
│                                          │   PromptTemplate  │ │
│                                          │   (templates)     │ │
│                                          └────────┬──────────┘ │
│                                                   │             │
│                                          ┌────────▼──────────┐ │
│                                          │   ChatGroq LLM    │ │
│                                          │  LLaMA 3.1 8B     │ │
│                                          └────────┬──────────┘ │
│                                                   │             │
│                                          ┌────────▼──────────┐ │
│                                          │  Pydantic Parser  │ │
│                                          │ MCQ / FillBlank   │ │
│                                          └───────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### MLOps Pipeline

```
Developer Push
      │
      ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   GitHub    │────▶│   Jenkins    │────▶│  DockerHub   │
│  (source)   │     │  CI Pipeline │     │  (registry)  │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │   ArgoCD     │  ← GitOps: watches repo
                    │  (sync app)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Kubernetes  │
                    │  (GKE / any) │
                    └──────────────┘
```

---

## 📁 Project Structure

```
study-buddy-ai/
│
├── application.py              # Streamlit entry point
├── Dockerfile                  # Multi-stage container build
├── Jenkinsfile                 # CI/CD pipeline definition
├── requirements.txt            # Python dependencies (pinned)
├── setup.py                    # Package install config
├── .env.example                # Environment variable template
│
├── manifests/
│   ├── deployment.yaml         # K8s Deployment (replicas, probes, limits)
│   └── service.yaml            # K8s Service (NodePort → port 80)
│
└── src/
    ├── common/
    │   ├── custom_exception.py # Structured exception with file/line info
    │   └── logger.py           # Centralised logging (stdout, timestamped)
    │
    ├── config/
    │   └── settings.py         # All config via env vars (.env support)
    │
    ├── generator/
    │   └── question_generator.py  # LLM calls + retry + validation
    │
    ├── llm/
    │   └── groq_client.py      # ChatGroq factory
    │
    ├── models/
    │   └── question_schemas.py # Pydantic v2 schemas (MCQ + FillBlank)
    │
    ├── prompts/
    │   └── templates.py        # LangChain PromptTemplates
    │
    └── utils/
        └── helpers.py          # QuizManager class + rerun utility
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A free [Groq API key](https://console.groq.com/keys)

### 1. Clone the repo

```bash
git clone https://github.com/ArchanaChetan07/Study-Buddy-AI.git
cd Study-Buddy-AI
```

### 2. Set up environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Run the app

```bash
streamlit run application.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🐳 Docker

### Build & run locally

```bash
docker build -t study-buddy-ai .

docker run -p 8501:8501 \
  -e GROQ_API_KEY=your_key_here \
  study-buddy-ai
```

### Using Docker Compose (optional)

```yaml
# docker-compose.yml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
```

```bash
docker compose up
```

---

## ☸️ Kubernetes Deployment

### 1. Create the API key secret

```bash
kubectl create secret generic groq-api-secret \
  --from-literal=GROQ_API_KEY=your_key_here
```

### 2. Apply manifests

```bash
kubectl apply -f manifests/deployment.yaml
kubectl apply -f manifests/service.yaml
```

### 3. Verify

```bash
kubectl get pods          # 2 replicas running
kubectl get svc           # NodePort exposed
kubectl describe deployment study-buddy-ai
```

### 4. Access

```bash
minikube service study-buddy-ai-service --url
# or
kubectl port-forward svc/study-buddy-ai-service 8080:80
```

---

## 🔄 CI/CD Pipeline

The Jenkins pipeline runs automatically on every push to `main`:

| Stage | What it does |
|---|---|
| **Checkout** | Pulls latest code from GitHub |
| **Lint** | Runs `ruff` — fails on syntax/style errors |
| **Build** | Builds Docker image tagged `v{BUILD_NUMBER}` |
| **Security Scan** | Trivy scans image for HIGH/CRITICAL CVEs |
| **Push** | Pushes `v{N}` + `latest` tags to DockerHub |
| **Update Manifest** | `sed` replaces image tag in `deployment.yaml` |
| **Commit & Push** | Commits updated manifest back to GitHub |
| **Sync ArgoCD** | ArgoCD detects manifest change, deploys to K8s |
| **Wait for Health** | Waits for pods to reach healthy state before passing |

### Jenkins Setup

```bash
# Run Jenkins in Docker (DIND mode, same network as Minikube)
docker run -d --name jenkins \
  --network minikube \
  -p 8080:8080 -p 50000:50000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts
```

Required credentials in Jenkins:
- `github-token` — GitHub personal access token
- `dockerhub-token` — DockerHub access token
- `kubeconfig` — Kubernetes cluster kubeconfig file

---

## ⚙️ Configuration

All settings live in `src/config/settings.py` and are overridable via environment variables:

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Your Groq API key |
| `MODEL_NAME` | `llama-3.1-8b-instant` | Groq model to use |
| `TEMPERATURE` | `0.85` | LLM creativity (0 = deterministic, 1 = creative) |
| `MAX_RETRIES` | `3` | LLM retry attempts on parse failure |

> **Tip:** Swap `MODEL_NAME` to `llama-3.3-70b-versatile` for higher quality questions at slightly lower speed.

---

## 🧩 How Question Generation Works

```
1. User picks topic + difficulty + type
       │
       ▼
2. PromptTemplate fills in {topic} and {difficulty}
       │
       ▼
3. ChatGroq invokes LLaMA 3.1 → returns raw JSON string
       │
       ▼
4. PydanticOutputParser parses → MCQQuestion or FillBlankQuestion
       │
       ▼
5. Structural validation:
   MCQ  → exactly 4 options, correct_answer ∈ options
   Fill → question contains '___', answer is non-empty
       │
       ▼
6. On failure → retry (up to MAX_RETRIES times)
       │
       ▼
7. Valid question appended to QuizManager.questions[]
```

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit 1.35+ |
| **LLM Inference** | Groq Cloud (LLaMA 3.1 8B Instant) |
| **LLM Framework** | LangChain 0.2 + langchain-groq |
| **Data Validation** | Pydantic v2 |
| **Data Processing** | Pandas |
| **Containerisation** | Docker (multi-stage, python:3.11-slim) |
| **Orchestration** | Kubernetes (GKE / Minikube) |
| **CI** | Jenkins |
| **CD / GitOps** | ArgoCD |
| **Security Scan** | Trivy (Aqua Security) |
| **Linting** | Ruff |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes and add tests if applicable
4. Ensure `ruff check .` passes with no errors
5. Commit with a conventional commit message: `feat: add topic suggestions`
6. Open a pull request against `main`

