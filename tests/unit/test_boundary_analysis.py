"""Test suy diễn biên/âm bản (BVA) — thuần, offline."""
from src.agents.test_design_agent import TestDesignAgent
from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCase, TestCaseDraft, TestType
from src.services.boundary_analysis import derive_boundary_cases, parse_bounds
from src.services.llm_client import MockLLMClient


def test_parse_bounds_patterns():
    assert parse_bounds("Mật khẩu 8-20 ký tự")[0] == {
        "kind": "range", "lo": 8, "hi": 20, "unit": "ký tự", "excerpt": "Mật khẩu 8-20 ký tự"}
    assert parse_bounds("từ 18 đến 65")[0]["kind"] == "range"
    assert parse_bounds("tối thiểu 8 ký tự")[0]["kind"] == "min"
    assert parse_bounds("không quá 100")[0] == {
        "kind": "max", "lo": None, "hi": 100, "unit": "", "excerpt": "không quá 100"}


def test_parse_bounds_no_number_returns_empty():
    assert parse_bounds("Phải nhập email hợp lệ") == []


def test_derive_range_gives_two_boundary_two_negative():
    req = StructuredRequirement(id="R", title="x", action="đăng ký", constraints=["Mật khẩu 8-20 ký tự"])
    cases = derive_boundary_cases(req)
    values = {(c.type, int(c.title.split("giá trị ")[1].split(" ")[0])) for c in cases}
    assert (TestType.BOUNDARY, 8) in values and (TestType.BOUNDARY, 20) in values
    assert (TestType.NEGATIVE, 7) in values and (TestType.NEGATIVE, 21) in values
    assert len(cases) == 4
    assert all(c.source_excerpt == "Mật khẩu 8-20 ký tự" for c in cases)


def test_derive_min_and_max_give_one_each():
    assert len(derive_boundary_cases(StructuredRequirement(id="R", title="x", action="a", constraints=["tối thiểu 8"]))) == 2
    assert len(derive_boundary_cases(StructuredRequirement(id="R", title="x", action="a", constraints=["tối đa 100"]))) == 2


def test_no_constraints_derives_nothing():
    assert derive_boundary_cases(StructuredRequirement(id="R", title="x", action="a")) == []


def test_design_agent_augments_with_boundary_cases():
    # mock chỉ trả 1 positive; requirement có ràng buộc số -> agent tự thêm biên/âm bản
    draft = TestCaseDraft(test_cases=[TestCase(title="Đăng ký hợp lệ", type=TestType.POSITIVE)])
    req = StructuredRequirement(id="REQ-001", title="Đăng ký", action="đăng ký tài khoản",
                                constraints=["Mật khẩu 8-20 ký tự"])
    result = TestDesignAgent(MockLLMClient(draft), model_name="mock").design(req)

    assert len(result.test_cases) == 5  # 1 positive + 4 biên/âm bản
    assert "boundary" in result.type_coverage and "negative" in result.type_coverage
    assert all(tc.id.startswith("REQ-001-TC-") for tc in result.test_cases)
    assert {link.to_id for link in result.trace_links} == {tc.id for tc in result.test_cases}
