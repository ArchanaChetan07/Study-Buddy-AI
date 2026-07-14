"""Pytest fixtures — force DEMO_MODE for offline green runs."""

import os

import pytest

os.environ["DEMO_MODE"] = "1"
os.environ.setdefault("GROQ_API_KEY", "")


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("GROQ_API_KEY", "")
