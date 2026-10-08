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


def _p(*acts):
    from src.models.playwright_artifacts import PlaywrightAction, PlaywrightPlan
    return PlaywrightPlan(actions=[PlaywrightAction(**a) for a in acts])


def test_repair_gate_maps_change_to_gate():
    from src.ui.review import repair_gate
    exp = {"type": "expect_text", "strategy": "css", "value": "#error", "arg": "Invalid"}
    assert repair_gate(_p(exp), _p({**exp, "arg": "Something"}), ["assertion_changed"]) == "AG-04"
    assert repair_gate(_p(exp), _p({**exp, "value": "#msg"}), ["assertion_changed"]) == "AG-03"
    assert repair_gate(_p(exp), _p(), ["step_removed"]) == "AG-05"
    click = {"type": "click", "strategy": "role", "value": "button", "role_name": "Login"}
    assert repair_gate(_p(click), _p({**click, "role_name": "Sign in"}), ["locator_changed"]) == "REPAIR-LOW"


def test_edited_test_case_none_when_unchanged():
    from src.models.test_case import TestStep
    from src.ui.review import edited_test_case
    tc = TestCase(id="T", title="a", type=TestType.POSITIVE, steps=[TestStep(action="x")], expected_result="ok")
    assert edited_test_case(tc, "a", "x\n", "ok") is None
    new = edited_test_case(tc, "a", "x\ny", "ok")
    assert [s.action for s in new.steps] == ["x", "y"]
