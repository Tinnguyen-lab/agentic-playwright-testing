"""Test approval model + is_approved (governance AG-01/AG-02)."""
from datetime import datetime, timedelta, timezone

from src.models.approval import ApprovalDecision, ApprovalStatus, is_approved


def test_is_approved_true_and_missing():
    ds = [ApprovalDecision(artifact_id="REQ-001", status=ApprovalStatus.APPROVED)]
    assert is_approved(ds, "REQ-001") is True
    assert is_approved(ds, "REQ-002") is False


def test_latest_decision_wins():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ds = [
        ApprovalDecision(artifact_id="REQ-001", status=ApprovalStatus.APPROVED, decided_at=t0),
        ApprovalDecision(artifact_id="REQ-001", status=ApprovalStatus.REJECTED, decided_at=t0 + timedelta(hours=1)),
    ]
    assert is_approved(ds, "REQ-001") is False


def test_rejected_not_approved():
    ds = [ApprovalDecision(artifact_id="REQ-001", status=ApprovalStatus.REJECTED)]
    assert is_approved(ds, "REQ-001") is False
