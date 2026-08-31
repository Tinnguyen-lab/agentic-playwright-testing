"""Test TestDesignAgent với MockLLMClient (offline)."""
from src.agents.test_design_agent import TestDesignAgent
from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCase, TestCaseDraft, TestType
from src.services.llm_client import MockLLMClient


def _draft() -> TestCaseDraft:
    return TestCaseDraft(test_cases=[
        TestCase(title="Đăng nhập hợp lệ", type=TestType.POSITIVE),
        TestCase(title="Sai mật khẩu", type=TestType.NEGATIVE),
    ])


def _agent() -> TestDesignAgent:
    return TestDesignAgent(MockLLMClient(_draft()), model_name="mock")


def _req() -> StructuredRequirement:
    return StructuredRequirement(
        id="REQ-001", title="Đăng nhập", actor="Người dùng",
        action="Đăng nhập bằng email và mật khẩu", expected_outcome="Vào trang chủ",
    )


def test_design_assigns_ids_and_traces():
    result = _agent().design(_req())
    assert [tc.id for tc in result.test_cases] == ["REQ-001-TC-01", "REQ-001-TC-02"]
    assert all(tc.requirement_id == "REQ-001" for tc in result.test_cases)
    assert result.source_requirement_id == "REQ-001"
    assert result.model_used == "mock"
    assert {(link.from_id, link.to_id) for link in result.trace_links} == {
        ("REQ-001", "REQ-001-TC-01"), ("REQ-001", "REQ-001-TC-02"),
    }


def test_design_type_coverage():
    assert _agent().design(_req()).type_coverage == ["negative", "positive"]


def test_design_empty_requirement_no_crash():
    result = _agent().design(StructuredRequirement(id="REQ-002", title="", action="   "))
    assert result.test_cases == []
    assert result.source_requirement_id == "REQ-002"


def test_design_reused_agent_no_id_collision():
    # cùng agent (mock trả cùng draft) chạy 2 requirement -> id không được đè lên nhau
    agent = _agent()
    r1 = agent.design(_req())
    r2 = agent.design(StructuredRequirement(id="REQ-009", title="X", action="làm X"))
    assert [tc.id for tc in r1.test_cases] == ["REQ-001-TC-01", "REQ-001-TC-02"]
    assert [tc.id for tc in r2.test_cases] == ["REQ-009-TC-01", "REQ-009-TC-02"]
    assert all(tc.requirement_id == "REQ-001" for tc in r1.test_cases)
