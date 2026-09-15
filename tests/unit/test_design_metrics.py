"""Test coverage/traceability metric cho Test Design (thuần, offline)."""
from src.evaluation.design_metrics import coverage_report
from src.models.test_case import TestCase, TestDesignResult, TestType, TraceLink


def _result(req_id, cases):
    tcs = [TestCase(id=f"{req_id}-TC-{i:02d}", requirement_id=req_id, title=t, type=ty)
           for i, (t, ty) in enumerate(cases, start=1)]
    links = [TraceLink(from_id=req_id, to_id=tc.id, link_type="requirement->test_case") for tc in tcs]
    return TestDesignResult(source_requirement_id=req_id, test_cases=tcs, trace_links=links)


def test_full_coverage_and_traceability():
    results = [
        _result("REQ-001", [("hợp lệ", TestType.POSITIVE), ("sai", TestType.NEGATIVE)]),
        _result("REQ-002", [("biên", TestType.BOUNDARY)]),
    ]
    rep = coverage_report(results, ["REQ-001", "REQ-002"])
    assert rep["requirement_coverage"] == 1.0
    assert rep["n_test_cases"] == 3
    assert rep["trace_completeness"] == 1.0
    assert rep["types_covered"] == ["boundary", "negative", "positive"]
    assert rep["uncovered_requirements"] == []


def test_partial_coverage():
    results = [
        _result("REQ-001", [("hợp lệ", TestType.POSITIVE)]),
        _result("REQ-002", []),  # không sinh case
    ]
    rep = coverage_report(results, ["REQ-001", "REQ-002"])
    assert rep["requirement_coverage"] == 0.5
    assert rep["uncovered_requirements"] == ["REQ-002"]
