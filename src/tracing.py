"""Lightweight structured tracing for tutoring agent runs."""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class Span:
    name: str
    start_ms: float
    end_ms: float | None = None
    attrs: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.end_ms is None:
            return None
        return round(self.end_ms - self.start_ms, 2)


@dataclass
class Trace:
    run_id: str
    spans: list[Span] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "spans": [
                {
                    "name": s.name,
                    "duration_ms": s.duration_ms,
                    "status": s.status,
                    "error": s.error,
                    "attrs": s.attrs,
                }
                for s in self.spans
            ],
        }


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


@contextmanager
def span(trace: Trace, name: str, **attrs: Any) -> Iterator[Span]:
    s = Span(name=name, start_ms=time.perf_counter() * 1000, attrs=dict(attrs))
    trace.spans.append(s)
    try:
        yield s
    except Exception as e:
        s.status = "error"
        s.error = f"{type(e).__name__}: {e}"
        raise
    finally:
        s.end_ms = time.perf_counter() * 1000
