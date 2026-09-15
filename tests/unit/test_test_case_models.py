"""Test models test case (Test Design Agent)."""
from src.models.test_case import TestCase, TestDesignResult, TestStep, TestType, TraceLink


def test_testcase_defaults_and_type():
    tc = TestCase(
        title="Đăng nhập hợp lệ",
        type=TestType.POSITIVE,
        steps=[TestStep(action="Nhập email và mật khẩu hợp lệ", expected="Vào trang chủ")],
    )
    assert tc.id == "" and tc.requirement_id == ""
    assert tc.type == TestType.POSITIVE
    assert tc.steps[0].expected == "Vào trang chủ"


def test_result_type_coverage():
    r = TestDesignResult(
        source_requirement_id="REQ-001",
        test_cases=[
            TestCase(title="a", type=TestType.POSITIVE),
            TestCase(title="b", type=TestType.NEGATIVE),
            TestCase(title="c", type=TestType.POSITIVE),
        ],
    )
    assert r.type_coverage == ["negative", "positive"]


def test_result_roundtrip_json():
    r = TestDesignResult(
        source_requirement_id="REQ-001",
        test_cases=[TestCase(title="a", type=TestType.BOUNDARY)],
        trace_links=[TraceLink(from_id="REQ-001", to_id="REQ-001-TC-01", link_type="requirement->test_case")],
    )
    r2 = TestDesignResult.model_validate_json(r.model_dump_json())
    assert r2.test_cases[0].type == TestType.BOUNDARY
    assert r2.trace_links[0].to_id == "REQ-001-TC-01"
