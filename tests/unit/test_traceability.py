"""Test traceability builder (thuần, offline)."""
from src.models.playwright_artifacts import ExecStatus, ExecutionResult
from src.models.repair import RepairOutcome, RepairProposal, RiskLevel
from src.models.test_case import TestCase, TestType
from src.services.traceability import build_report, render_markdown


def _tc(id_, req):
    return TestCase(id=id_, requirement_id=req, title="x", type=TestType.POSITIVE)


def test_coverage_and_orphans():
    req_ids = ["REQ-001", "REQ-002"]
    tcs = [_tc("REQ-001-TC-01", "REQ-001"), _tc("ORPHAN-TC", "REQ-999")]  # REQ-999 không có -> orphan
    execs = [ExecutionResult(test_case_id="REQ-001-TC-01", status=ExecStatus.PASSED)]
    rep = build_report(req_ids, tcs, execs, [])

    assert rep["requirement_coverage"] == 0.5   # REQ-002 chưa có test
    assert rep["executed_coverage"] == 0.5      # 1/2 test có execution
    assert rep["pass_rate"] == 1.0
    assert rep["orphans"]["test_cases"] == ["ORPHAN-TC"]


def test_chain_and_markdown_include_repair():
    tcs = [_tc("REQ-001-TC-01", "REQ-001")]
    execs = [ExecutionResult(test_case_id="REQ-001-TC-01", status=ExecStatus.FAILED)]
    repairs = [RepairProposal(test_case_id="REQ-001-TC-01", risk_level=RiskLevel.LOW, outcome=RepairOutcome.PROPOSED)]
    rep = build_report(["REQ-001"], tcs, execs, repairs)
    md = render_markdown(rep)
    assert "REQ-001-TC-01" in md and "proposed/low" in md
