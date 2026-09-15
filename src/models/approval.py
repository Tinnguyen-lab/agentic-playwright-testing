"""Approval model — governance human-in-the-loop (architecture v0.1, mục 5.9, AG-01..AG-07).

Không dùng LLM thay quyết định người dùng; chỉ lưu quyết định + version artifact.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalDecision(BaseModel):
    artifact_id: str
    artifact_version: int = 1
    status: ApprovalStatus
    reason: str = ""
    decided_by: str = ""
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def is_approved(decisions: list[ApprovalDecision], artifact_id: str) -> bool:
    """artifact_id được coi là approved nếu quyết định MỚI NHẤT của nó là APPROVED."""
    latest = None
    for d in decisions:
        if d.artifact_id == artifact_id and (latest is None or d.decided_at >= latest.decided_at):
            latest = d
    return latest is not None and latest.status == ApprovalStatus.APPROVED
