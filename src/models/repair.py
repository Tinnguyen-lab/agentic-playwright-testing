"""Artifacts cho Repair Agent (architecture v0.1, mục 5.8 + repair policy mục 9)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from src.models.playwright_artifacts import PlaywrightPlan


class FailureType(str, Enum):
    LOCATOR_NOT_FOUND = "locator_not_found"
    TIMEOUT = "timeout"
    ASSERTION_FAILED = "assertion_failed"
    NAVIGATION = "navigation"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


class RepairOutcome(str, Enum):
    PROPOSED = "proposed"
    BLOCKED_FOR_REVIEW = "blocked_for_review"
    REFUSED = "refused"
    NOT_NEEDED = "not_needed"


class RepairDraft(BaseModel):
    """Đầu ra thô của LLM: plan sửa + phân loại failure."""

    new_plan: PlaywrightPlan = Field(default_factory=PlaywrightPlan)
    failure_type: FailureType = FailureType.UNKNOWN
    reason: str = ""


class RepairProposal(BaseModel):
    test_case_id: str = ""
    failure_type: FailureType = FailureType.UNKNOWN
    risk_level: RiskLevel = RiskLevel.LOW
    semantic_impact: bool = False
    changed_kinds: list[str] = Field(default_factory=list)
    diff: str = ""
    reason: str = ""
    evidence: list[str] = Field(default_factory=list)
    requires_approval: bool = True
    outcome: RepairOutcome = RepairOutcome.PROPOSED
