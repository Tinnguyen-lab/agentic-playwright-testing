"""Test helper thuần của UI review (offline, không cần streamlit)."""
from src.models.approval import ApprovalDecision, ApprovalStatus
from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCase, TestType
from src.ui.review import approved_requirement_ids, approved_test_case_ids


def test_approved_requirement_ids_latest_decision_wins():
    reqs = [StructuredRequirement(id="REQ-001", title="a", action="x"),
            StructuredRequirement(id="REQ-002", title="b", action="y")]
    decisions = [
        ApprovalDecision(artifact_id="REQ-001", status=ApprovalStatus.REJECTED),
        ApprovalDecision(artifact_id="REQ-001", status=ApprovalStatus.APPROVED),  # mới hơn -> thắng
        ApprovalDecision(artifact_id="REQ-002", status=ApprovalStatus.REJECTED),
    ]
    assert approved_requirement_ids(reqs, decisions) == ["REQ-001"]


def test_approved_test_case_ids():
    tcs = [TestCase(id="REQ-001-TC-01", title="a", type=TestType.POSITIVE),
           TestCase(id="REQ-001-TC-02", title="b", type=TestType.NEGATIVE)]
    decisions = [ApprovalDecision(artifact_id="REQ-001-TC-01", status=ApprovalStatus.APPROVED)]
    assert approved_test_case_ids(tcs, decisions) == ["REQ-001-TC-01"]
