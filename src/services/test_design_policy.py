"""Runtime binding for the project-local QA prompt skill.

The agent imports this policy for every LLM request, so the skill is executable
project policy rather than documentation that a developer must remember to copy.
"""
from __future__ import annotations

from pathlib import Path


_POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills" / "qa-prompt-guideline" / "references" / "runtime-test-design-policy.md"
)

_FALLBACK_POLICY = """Analyse coverage before generating cases. Use requirement-backed or clearly review-gated exploratory cases; never invent an oracle."""


def load_test_design_policy() -> str:
    """Return the checked-in skill policy without making startup depend on I/O success."""
    try:
        return _POLICY_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return _FALLBACK_POLICY


TEST_DESIGN_RUNTIME_POLICY = load_test_design_policy()
