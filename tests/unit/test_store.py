"""Repository trên SQLite in-memory: version, quyết định append-only, truy vết, sự kiện UI."""
import pytest

from src.database import session_factory
from src.models.approval import is_approved
from src.models.playwright_artifacts import ExecStatus, ExecutionResult, GeneratedScript, PlaywrightPlan
from src.models.repair import RepairProposal, RiskLevel
from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCase, TestType
from src.repositories.store import Store


@pytest.fixture
def store():
    return Store(session_factory("sqlite://"))


def _req(action="Đăng nhập"):
    return StructuredRequirement(id="REQ-001", title="Login", action=action)


def test_versions_only_bump_on_change(store):
    pid = store.get_or_create_project("demo", "http://x")
    assert store.get_or_create_project("demo") == pid
    assert store.save_requirements(pid, [_req()]) == {"REQ-001": 1}
    assert store.save_requirements(pid, [_req()]) == {"REQ-001": 1}  # cùng nội dung
    assert store.save_requirements(pid, [_req("Đăng nhập bằng email")]) == {"REQ-001": 2}
    assert store.latest_requirements(pid)[0].action == "Đăng nhập bằng email"


def test_decisions_append_only_latest_wins(store):
    pid = store.get_or_create_project("demo")
    store.record_decision(pid, "AG-01", "requirement", "REQ-001", approved=True, decided_by="sang")
    store.record_decision(pid, "AG-01", "requirement", "REQ-001", approved=False, reason="còn mơ hồ")
    ds = store.decisions(pid, "AG-01")
    assert len(ds) == 2 and not is_approved(ds, "REQ-001")


def test_trace_chain_requirement_to_repair(store):
    pid = store.get_or_create_project("demo")
    tc = TestCase(id="REQ-001-TC-01", requirement_id="REQ-001", title="t", type=TestType.POSITIVE)
    store.save_test_cases(pid, [tc])
    sid = store.save_script(pid, PlaywrightPlan(), GeneratedScript(test_case_id=tc.id, code="pass"))
    eid = store.save_execution(pid, ExecutionResult(test_case_id=tc.id, status=ExecStatus.FAILED), sid)
    store.save_repair(pid, RepairProposal(test_case_id=tc.id, risk_level=RiskLevel.LOW), eid)
    rels = [link[2] for link in store.trace_links(pid)]
    assert rels == ["verified_by", "implemented_by", "executed_as", "repaired_by"]
    assert store.repairs(pid)[0][1].risk_level == RiskLevel.LOW


def test_ui_events_by_session(store):
    pid = store.get_or_create_project("demo")
    store.log_event(pid, "s1", "edit_test_case", actor="p1", field="steps")
    store.log_event(pid, "s2", "approve", actor="p2")
    assert [e.event for e in store.events(pid, "s1")] == ["edit_test_case"]
