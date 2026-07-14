"""Prometheus metrics for Study Buddy AI (Streamlit companion HTTP server)."""
from __future__ import annotations

import os
import threading
from typing import Optional

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
    start_http_server,
)

QUIZ_REQUESTS = Counter(
    "studybuddy_quiz_requests_total",
    "Quiz generation requests",
    ["status", "question_type"],
)
QUIZ_ERRORS = Counter(
    "studybuddy_quiz_errors_total",
    "Quiz generation errors",
)
QUIZ_REVISIONS = Counter(
    "studybuddy_quiz_revisions_total",
    "Agent revise-loop invocations",
)
QUIZ_LATENCY = Histogram(
    "studybuddy_quiz_latency_seconds",
    "Quiz generation latency seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
AGENT_TOOL_STEPS = Histogram(
    "studybuddy_agent_tool_steps",
    "Tool steps used per generation run (budget max 8)",
    buckets=(1, 2, 3, 4, 5, 6, 7, 8),
)

_server_started = False
_lock = threading.Lock()


def start_metrics_server(port: Optional[int] = None) -> int:
    """Idempotent start of a Prometheus scrape HTTP server (default port 9090)."""
    global _server_started
    port = int(port or os.getenv("METRICS_PORT", "9090"))
    with _lock:
        if _server_started:
            return port
        start_http_server(port)
        _server_started = True
        return port


def record_quiz_generation(
    *,
    status: str,
    question_type: str,
    latency_s: float,
    revisions: int = 0,
    tool_steps: int = 0,
) -> None:
    QUIZ_REQUESTS.labels(status=status, question_type=question_type).inc()
    QUIZ_LATENCY.observe(max(0.0, latency_s))
    if revisions:
        QUIZ_REVISIONS.inc(revisions)
    if status == "error":
        QUIZ_ERRORS.inc()
    if tool_steps:
        AGENT_TOOL_STEPS.observe(tool_steps)


def metrics_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
