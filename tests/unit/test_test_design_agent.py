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
    result = _agent().design(_req(), expanded=False)
    assert [tc.id for tc in result.test_cases] == [
        f"REQ-001-TC-{index:02d}" for index in range(1, len(result.test_cases) + 1)
    ]
    assert len(result.test_cases) >= 6
    assert all(tc.requirement_id == "REQ-001" for tc in result.test_cases)
    assert result.source_requirement_id == "REQ-001"
    assert result.model_used == "mock"
    assert {(link.from_id, link.to_id) for link in result.trace_links} == {
        ("REQ-001", tc.id) for tc in result.test_cases
    }


def test_design_type_coverage():
    coverage = _agent().design(_req(), expanded=False).type_coverage
    assert {"negative", "positive"}.issubset(coverage)


def test_design_empty_requirement_no_crash():
    result = _agent().design(StructuredRequirement(id="REQ-002", title="", action="   "))
    assert result.test_cases == []
    assert result.source_requirement_id == "REQ-002"


def test_design_reused_agent_no_id_collision():
    # cùng agent (mock trả cùng draft) chạy 2 requirement -> id không được đè lên nhau
    agent = _agent()
    r1 = agent.design(_req(), expanded=False)
    r2 = agent.design(StructuredRequirement(id="REQ-009", title="X", action="làm X"), expanded=False)
    assert all(tc.id.startswith("REQ-001-TC-") for tc in r1.test_cases)
    assert all(tc.id.startswith("REQ-009-TC-") for tc in r2.test_cases)
    assert all(tc.requirement_id == "REQ-001" for tc in r1.test_cases)


def test_design_deduplicates_identical_cases():
    duplicate = TestCaseDraft(test_cases=[
        TestCase(title="Đăng nhập", type=TestType.POSITIVE, expected_result="Vào trang chủ"),
        TestCase(title="đăng nhập", type=TestType.POSITIVE, expected_result="vào trang chủ"),
    ])
    result = TestDesignAgent(MockLLMClient(duplicate)).design(_req(), expanded=False)
    assert sum(tc.title.casefold() == "đăng nhập" for tc in result.test_cases) == 1


def test_design_uses_deterministic_boundary_cases_not_llm_guesses():
    draft = TestCaseDraft(test_cases=[TestCase(title="LLM boundary", type=TestType.BOUNDARY)])
    req = StructuredRequirement(id="R", title="x", action="nhập", constraints=["từ 1 đến 2 ký tự"])
    result = TestDesignAgent(MockLLMClient(draft), model_name="mock").design(req, expanded=False)
    # Four deterministic BVA cases plus positive and exploratory review ideas.
    assert len(result.test_cases) >= 5
    assert all(tc.title != "LLM boundary" for tc in result.test_cases)


def test_expanded_prompt_requires_review_marker_for_assumptions():
    prompt = TestDesignAgent._build_user_prompt(_req(), expanded=True)
    assert "review_required=true" in prompt
    assert "6–10 case" in prompt


def test_prompt_follows_persona_task_context_format_and_coverage_plan():
    prompt = TestDesignAgent._build_user_prompt(_req(), expanded=True)
    assert "VAI TRÒ:" in prompt
    assert "NHIỆM VỤ:" in prompt
    assert "NGỮ CẢNH:" in prompt
    assert "ĐỊNH DẠNG:" in prompt
    assert "CÁCH LẬP KẾ HOẠCH:" in prompt
    assert "expected_result rỗng" in prompt


def test_default_design_mode_is_expanded():
    prompt = TestDesignAgent._build_user_prompt(_req())
    assert "CHẾ ĐỘ EXPANDED" in prompt


def test_review_marker_is_preserved_in_expanded_result():
    draft = TestCaseDraft(test_cases=[TestCase(title="Retry after timeout", type=TestType.ALTERNATIVE_FLOW,
                                                review_required=True, review_note="Retry policy is not specified.")])
    result = TestDesignAgent(MockLLMClient(draft)).design(_req(), expanded=True)
    assert result.test_cases[0].review_required is True
    assert "Retry policy is not specified." in result.test_cases[0].review_note


def test_expanded_mode_retries_once_when_llm_returns_too_few_cases():
    first = TestCaseDraft(test_cases=[TestCase(title="Happy", type=TestType.POSITIVE)])
    second = TestCaseDraft(test_cases=[
        TestCase(title="Happy", type=TestType.POSITIVE),
        TestCase(title="Validation candidate", type=TestType.NEGATIVE, review_required=True,
                 review_note="The expected validation behavior is not specified."),
        TestCase(title="Alternative candidate", type=TestType.ALTERNATIVE_FLOW, review_required=True,
                 review_note="The alternate flow is not specified."),
    ])

    class SequencedLLM:
        def __init__(self):
            self.responses = [first, second]
            self.prompts = []

        def structured_completion(self, _system, prompt, _schema):
            self.prompts.append(prompt)
            return self.responses.pop(0)

    llm = SequencedLLM()
    result = TestDesignAgent(llm).design(_req(), expanded=True)
    assert len(llm.prompts) == 2
    assert "Lần trả lời trước chỉ có 1" in llm.prompts[1]
    assert len(result.test_cases) >= 6
    assert sum(tc.review_required for tc in result.test_cases) >= 2


def test_expanded_adds_review_gated_exploratory_ideas_when_evidence_is_sparse():
    result = TestDesignAgent(MockLLMClient(TestCaseDraft())).design(_req(), expanded=True)
    exploratory = [tc for tc in result.test_cases if tc.scenario_id == "EXPLORE"]
    assert len(result.test_cases) >= 6
    assert exploratory
    assert all(tc.review_required and not tc.expected_result for tc in exploratory)
    assert all("Exploratory heuristic" in tc.review_note for tc in exploratory)


def test_expanded_gates_llm_negative_drafts_even_if_model_marks_them_approved():
    draft = TestCaseDraft(test_cases=[
        TestCase(title="Happy", type=TestType.POSITIVE, expected_result="Known outcome"),
        TestCase(title="Invented validation", type=TestType.NEGATIVE,
                 expected_result="Invented error message", review_required=False),
    ])
    result = TestDesignAgent(MockLLMClient(draft)).design(_req(), expanded=True)
    negative = next(tc for tc in result.test_cases if tc.title == "Invented validation")
    assert negative.review_required is True
    assert negative.expected_result == ""
    assert "Exploratory risk case" in negative.review_note


def test_expanded_keeps_one_representative_per_inferred_risk_type():
    draft = TestCaseDraft(test_cases=[
        TestCase(title="Happy", type=TestType.POSITIVE),
        TestCase(title="Wrong password", type=TestType.NEGATIVE),
        TestCase(title="Blank password", type=TestType.NEGATIVE),
        TestCase(title="Unicode password", type=TestType.ERROR_GUESSING),
        TestCase(title="Whitespace password", type=TestType.ERROR_GUESSING),
    ])
    result = TestDesignAgent(MockLLMClient(draft)).design(_req())
    llm_risks = [tc for tc in result.test_cases if tc.scenario_id != "EXPLORE" and tc.type != TestType.POSITIVE]
    assert [tc.title for tc in llm_risks] == ["Wrong password", "Unicode password"]


def test_design_adds_positive_fallback_when_llm_only_returns_negative():
    draft = TestCaseDraft(test_cases=[TestCase(title="Bad input", type=TestType.NEGATIVE)])
    result = TestDesignAgent(MockLLMClient(draft)).design(_req())
    assert any(tc.type == TestType.POSITIVE for tc in result.test_cases)
    assert {tc.scenario_id for tc in result.test_cases if tc.type == TestType.POSITIVE} == {"SC-01"}


def test_design_splits_explicit_alternative_flow_keeps_one_main_positive_fallback():
    req = _req().model_copy(update={"alternative_flows": ["User cancels before submit"]})
    result = TestDesignAgent(MockLLMClient(TestCaseDraft())).design(req)
    positives = [tc for tc in result.test_cases if tc.type == TestType.POSITIVE]
    assert {tc.scenario_id for tc in positives} == {"SC-01"}
    assert positives[0].review_required is False
