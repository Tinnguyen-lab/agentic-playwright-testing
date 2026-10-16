"""Test Design Agent (architecture v0.1, mục 5.5).

Vào: một requirement ĐÃ ĐƯỢC PHÊ DUYỆT. Ra: TestDesignResult (test case + trace link).
Nguyên tắc: chỉ sinh từ căn cứ trong requirement; không tạo expected result vượt requirement.
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCase, TestCaseDraft, TestDesignResult, TestStep, TestType, TraceLink
from src.services.boundary_analysis import derive_boundary_cases
from src.services.llm_client import LLMClient
from src.services.scenario_decomposition import decompose
from src.services.test_design_policy import TEST_DESIGN_RUNTIME_POLICY
from src.services.test_triage import evaluate_test_case

MIN_EXPANDED_CASES = 6

SYSTEM_PROMPT = f"""\
Bạn là kỹ sư thiết kế kiểm thử. Nhận MỘT yêu cầu ĐÃ ĐƯỢC PHÊ DUYỆT và sinh các test case
kiểm thử chức năng.

QUY TẮC BẮT BUỘC:
- Sinh test case theo các loại KHI CÓ CĂN CỨ từ yêu cầu: positive, negative, boundary,
  error_guessing, alternative_flow. KHÔNG bịa loại không có căn cứ.
- Mỗi test case gồm: title, type, preconditions, steps (mỗi step có action và expected),
  expected_result.
- KHÔNG tạo expected_result vượt quá phạm vi requirement đã duyệt.
- negative / error_guessing / alternative_flow: CHỈ sinh khi requirement NÊU hệ thống phản ứng thế nào trong trường
  hợp đó (vd "sai thì hiển thị lỗi", "quá 5 cuốn thì từ chối"). Requirement không nói thì KHÔNG tự đặt kết quả
  mong đợi — bỏ qua case đó (chỗ thiếu này thuộc về làm rõ yêu cầu, không phải test).
- Bám actor/precondition/action/expected_outcome của requirement.
- Hệ thống TỰ bổ sung case biên (boundary) từ ràng buộc SỐ; hãy tập trung positive và
  negative theo ngữ nghĩa, không cần liệt kê từng giá trị biên số.
- Ở chế độ Expanded, bạn có thể đề xuất biến thể hữu ích chưa có oracle CHỈ khi để
  expected_result rỗng, review_required=true và review_note nói chính xác điều cần người duyệt xác nhận.
  Đó là ứng viên để thảo luận, không phải bằng chứng yêu cầu hay case đã được xác minh.
- KHÔNG gán ID (hệ thống tự gán).
- Với mỗi case, đề xuất priority P0/P1/P2/P3 (mức ưu tiên xử lý) và severity
  critical/high/medium/low (tác động NẾU hành vi sai), kèm triage_reason ngắn.
  P0 chỉ dành cho rủi ro mất dữ liệu, truy cập trái phép hoặc thiệt hại tài chính
  có căn cứ; không đồng nhất mức ưu tiên với kết quả chạy hay một lỗi đã xác nhận.

CHÍNH SÁCH RUNTIME TỪ SKILL:
{TEST_DESIGN_RUNTIME_POLICY}

Trả về JSON gồm: test_cases[].\
"""


class TestDesignAgent:
    def __init__(self, llm: LLMClient, model_name: str = "unknown"):
        self._llm = llm
        self._model_name = model_name

    def design(self, requirement: StructuredRequirement, expanded: bool = True) -> TestDesignResult:
        # Compatibility argument only: exploratory coverage is a product-wide
        # policy and cannot be disabled by a caller.
        expanded = True
        if not requirement.action or not requirement.action.strip():
            return self._empty_result(requirement.id)

        scenarios = decompose(requirement)
        user_prompt = self._build_user_prompt(requirement, scenarios, expanded=expanded)
        draft = self._llm.structured_completion(SYSTEM_PROMPT, user_prompt, TestCaseDraft)
        # Expanded is the reviewer-facing ideation mode.  Models often return
        # only the obvious happy path even when asked for variants, so give one
        # bounded retry.  The returned candidates remain review-gated whenever
        # their oracle is not stated in the approved requirement.
        if expanded and len(draft.test_cases) < MIN_EXPANDED_CASES:
            draft = self._llm.structured_completion(
                SYSTEM_PROMPT,
                self._expanded_retry_prompt(requirement, scenarios, len(draft.test_cases)),
                TestCaseDraft,
            )

        # Numeric BVA is deterministic below.  Discard LLM boundary cases so an
        # approximate value (for example 2 instead of the documented 1/2000)
        # cannot be presented as evidence-backed coverage.
        llm_cases = [tc for tc in draft.test_cases if tc.type != TestType.BOUNDARY]
        llm_cases = [tc.model_copy(update={"scenario_id": tc.scenario_id or scenarios[0].id}) for tc in llm_cases]
        if expanded:
            llm_cases = self._gate_exploratory_drafts(llm_cases)
            llm_cases = self._select_distinct_exploratory_drafts(llm_cases)
        evidence_backed = self._deduplicate(
            llm_cases + derive_boundary_cases(requirement) +
            self._missing_positive_cases(requirement, scenarios, llm_cases)
        )
        exploratory = self._exploratory_candidates(requirement, evidence_backed) if expanded else []
        all_cases = self._deduplicate(evidence_backed + exploratory)

        cases = []
        links = []
        for index, tc in enumerate(all_cases, start=1):
            tc_id = f"{requirement.id}-TC-{index:02d}"
            identified = tc.model_copy(update={"id": tc_id, "requirement_id": requirement.id})
            cases.append(evaluate_test_case(identified))
            links.append(TraceLink(from_id=requirement.id, to_id=tc_id, link_type="requirement->test_case"))

        return TestDesignResult(
            source_requirement_id=requirement.id,
            test_cases=cases,
            trace_links=links,
            model_used=self._model_name,
            created_at=datetime.now(timezone.utc),
        )

    def _empty_result(self, requirement_id: str) -> TestDesignResult:
        return TestDesignResult(
            source_requirement_id=requirement_id,
            model_used=self._model_name,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _missing_positive_cases(requirement: StructuredRequirement, scenarios, cases: list[TestCase]) -> list[TestCase]:
        """Fail safe: retain one reviewable happy-path case for the main scenario only."""
        if any(tc.type == TestType.POSITIVE for tc in cases):
            return []
        scenario = scenarios[0]
        missing_oracle = not bool(scenario.expected_result)
        return [TestCase(
            title=f"{requirement.title} — {scenario.title}", type=TestType.POSITIVE,
            scenario_id=scenario.id,
            preconditions=[requirement.precondition] if requirement.precondition else [],
            steps=[TestStep(action=step) for step in scenario.flow],
            expected_result=scenario.expected_result,
            source_excerpt=requirement.source_excerpt,
            review_required=missing_oracle,
            review_note="Expected result for this scenario is not specified in the requirement." if missing_oracle else "",
        )]

    @staticmethod
    def _deduplicate(cases):
        """Remove semantically identical drafts before assigning stable IDs."""
        kept, seen = [], set()
        for tc in cases:
            key = (tc.scenario_id, tc.type.value, tc.title.casefold().strip(),
                   tuple(step.action.casefold().strip() for step in tc.steps),
                   tc.expected_result.casefold().strip())
            if key not in seen:
                seen.add(key)
                kept.append(tc)
        return kept

    @staticmethod
    def _gate_exploratory_drafts(cases: list[TestCase]) -> list[TestCase]:
        """Keep LLM-suggested risk cases from masquerading as documented behavior.

        A positive case can directly represent the approved outcome.  In Expanded
        mode, non-positive LLM cases are ideas unless a reviewer explicitly
        validates their oracle; clearing the oracle prevents an invented PASS.
        Deterministic boundary cases are added later from explicit constraints.
        """
        gated = []
        for case in cases:
            if case.type == TestType.POSITIVE:
                gated.append(case)
                continue
            note = case.review_note.strip()
            policy_note = (
                "Exploratory risk case: its expected behavior is not accepted as requirement evidence. "
                "Reviewer must validate the setup and oracle before approval."
            )
            gated.append(case.model_copy(update={
                "expected_result": "",
                "review_required": True,
                "review_note": f"{note} {policy_note}".strip(),
            }))
        return gated

    @staticmethod
    def _select_distinct_exploratory_drafts(cases: list[TestCase]) -> list[TestCase]:
        """Keep one representative per inferred risk type before adding other techniques.

        Models often turn one login form into many near-identical password
        mutations.  They are useful ideas, but a reviewer gets better coverage
        from a compact risk portfolio than from six copies of the same hypothesis.
        """
        selected: list[TestCase] = []
        seen_inferred_types: set[TestType] = set()
        for case in cases:
            if case.type == TestType.POSITIVE:
                selected.append(case)
                continue
            if case.type in seen_inferred_types:
                continue
            seen_inferred_types.add(case.type)
            selected.append(case)
        return selected

    @staticmethod
    def _exploratory_candidates(requirement: StructuredRequirement, existing_cases: list[TestCase]) -> list[TestCase]:
        """Guarantee a review-gated portfolio of named testing techniques."""
        needed = max(0, MIN_EXPANDED_CASES - len(existing_cases))

        def idea(title: str, test_type: TestType, action: str, focus: str) -> TestCase:
            return TestCase(
                title=f"Khám phá — {requirement.title}: {title}", type=test_type,
                scenario_id="EXPLORE", preconditions=[requirement.precondition] if requirement.precondition else [],
                steps=[TestStep(action=action)], source_excerpt=requirement.source_excerpt,
                review_required=True,
                review_note=(f"Exploratory heuristic ({focus}), not a requirement-backed oracle. "
                             "Reviewer must define target-specific setup, expected result and acceptance criteria before approval."),
            )

        existing_types = {case.type for case in existing_cases}
        taxonomy = [
            idea("Negative testing", TestType.NEGATIVE,
                 "Thử một dữ liệu hoặc điều kiện không hợp lệ liên quan trực tiếp đến tác vụ.",
                 "negative testing"),
            idea("Error guessing", TestType.ERROR_GUESSING,
                 "Dựa trên lỗi thường gặp, thử để trống, khoảng trắng, thao tác lặp hoặc dữ liệu bất thường phù hợp.",
                 "error guessing"),
            idea("Giá trị biên", TestType.BOUNDARY,
                 "Xác định giới hạn đầu vào hoặc số lượng liên quan; thử ngay tại biên và ngay ngoài biên.",
                 "boundary value analysis"),
            idea("Phân vùng tương đương", TestType.EQUIVALENCE_PARTITION,
                 "Chọn một đại diện cho mỗi lớp dữ liệu hợp lệ, không hợp lệ và rỗng có liên quan.",
                 "equivalence partitioning"),
            idea("Chuyển vùng trạng thái", TestType.STATE_TRANSITION,
                 "Thử tác vụ khi trạng thái trước/sau khác nhau, như mới vào trang, đã thao tác, tải lại hoặc quay lại.",
                 "state-transition testing"),
            idea("Khám phá UI/UX và accessibility", TestType.EXPLORATORY,
                 "Dùng bàn phím, kiểm tra focus, thông báo, viewport hẹp và khả năng hoàn tất nhiệm vụ của người dùng.",
                 "exploratory UI/UX and accessibility"),
        ]
        missing_techniques = [case for case in taxonomy if case.type not in existing_types]
        # When the LLM already covers the taxonomy, retain a small extra budget
        # for a separate resilience charter rather than cosmetic data mutations.
        extras = [
            idea("Khả năng phục hồi", TestType.ALTERNATIVE_FLOW,
                 "Quan sát hành vi khi phản hồi chậm, tải lại hoặc chuyển trang trong lúc tác vụ đang xử lý.",
                 "loading, recovery and user feedback"),
        ]
        return missing_techniques + extras[:max(0, needed - len(missing_techniques))]

    @staticmethod
    def _build_user_prompt(requirement: StructuredRequirement, scenarios=None, expanded: bool = True) -> str:
        # Keep the private helper consistent with the public, always-expanded policy.
        expanded = True
        scenarios = scenarios or decompose(requirement)
        prompt = (
            "VAI TRÒ: Bạn là kỹ sư QA thiết kế test có khả năng truy vết.\n"
            "NHIỆM VỤ: Thiết kế test case cho đúng MỘT yêu cầu đã duyệt dưới đây.\n"
            "NGỮ CẢNH: Chỉ các dữ kiện trong khối REQUIREMENT và SCENARIOS là bằng chứng.\n"
            "ĐỊNH DẠNG: Trả đúng JSON TestCaseDraft; không viết giải thích ngoài JSON.\n\n"
            "REQUIREMENT:\n"
            f"- id: {requirement.id}\n"
            f"- title: {requirement.title}\n"
            f"- actor: {requirement.actor or '—'}\n"
            f"- precondition: {requirement.precondition or '—'}\n"
            f"- main_flow: {' | '.join(requirement.main_flow) or '—'}\n"
            f"- alternative_flows: {' | '.join(requirement.alternative_flows) or '—'}\n"
            f"- action: {requirement.action}\n"
            f"- expected_outcome: {requirement.expected_outcome or '—'}\n"
            f"- postconditions: {' | '.join(requirement.postconditions) or '—'}\n"
            f"- business_rules: {' | '.join(requirement.business_rules) or '—'}\n"
            f"- constraints: {', '.join(requirement.constraints) or '—'}"
        )
        prompt += "\n- scenarios (controlled, use scenario_id exactly):\n" + "\n".join(
            f"  - {scenario.id}: {scenario.title}; flow={' | '.join(scenario.flow)}; expected={scenario.expected_result or '—'}"
            for scenario in scenarios
        )
        prompt += (
            "\n\nCÁCH LẬP KẾ HOẠCH: Trước khi xuất JSON, hãy lập coverage plan nội bộ: "
            "(1) giữ một positive case cho mỗi scenario; (2) tìm rule, alternative flow, trạng thái hoặc lớp dữ liệu "
            "được nêu rõ để tạo case khác biệt; (3) kiểm tra mọi oracle có nguồn. "
            "Hai case chỉ khác tên hoặc lặp lại cùng action/data/state không được xem là khác biệt."
        )
        if expanded:
            prompt += (
                "\n\nCHẾ ĐỘ EXPANDED (cần người duyệt):\n"
                "- Mục tiêu: trả 6–10 case KHÁC BIỆT. Phân bổ trước: ít nhất một happy path; sau đó ưu tiên "
                "validation/error đã nêu, alternative flow đã nêu, business rule, state transition hoặc boundary có căn cứ.\n"
                "- Bắt buộc bao phủ và gán đúng type khi phù hợp: negative, error_guessing, boundary, "
                "equivalence_partition, state_transition, exploratory (UI/UX/accessibility).\n"
                "- Nếu một scenario hữu ích nhưng requirement chưa nêu phản ứng/expected result, vẫn có thể đề xuất "
                "NHƯNG phải đặt review_required=true, review_note nêu rõ giả định cần xác nhận, và không được mô tả "
                "giả định đó như requirement đã được chứng minh.\n"
                "- Với ứng viên chưa có oracle: để expected_result rỗng. Case có đầy đủ căn cứ phải đặt "
                "review_required=false. Không tạo case trùng lặp.\n"
                "- Đánh giá priority và severity riêng cho mỗi case dựa trên tác động/rủi ro, "
                "ghi rõ triage_reason. Đây là đề xuất để người duyệt kiểm tra, không phải lỗi đã xác nhận."
            )
        return prompt

    @classmethod
    def _expanded_retry_prompt(cls, requirement: StructuredRequirement, scenarios, received: int) -> str:
        """Ask once more when an expanded response did not meet its contract."""
        return cls._build_user_prompt(requirement, scenarios, expanded=True) + (
            f"\n\nLần trả lời trước chỉ có {received} test case. Hãy trả về TỪ 6 ĐẾN 10 test case PHÂN BIỆT. "
            "Giữ ít nhất một positive case bám requirement. Với biến thể validation, alternative hoặc state "
            "chưa có expected result trong requirement, không được bịa oracle: đặt expected_result rỗng, "
            "review_required=true và review_note giải thích chính xác điều cần người duyệt xác nhận."
        )
