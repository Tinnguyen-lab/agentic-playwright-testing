"""Test Design Agent (architecture v0.1, mục 5.5).

Vào: một requirement ĐÃ ĐƯỢC PHÊ DUYỆT. Ra: TestDesignResult (test case + trace link).
Nguyên tắc: chỉ sinh từ căn cứ trong requirement; không tạo expected result vượt requirement.
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCaseDraft, TestDesignResult, TraceLink
from src.services.llm_client import LLMClient

SYSTEM_PROMPT = """\
Bạn là kỹ sư thiết kế kiểm thử. Nhận MỘT yêu cầu ĐÃ ĐƯỢC PHÊ DUYỆT và sinh các test case
kiểm thử chức năng.

QUY TẮC BẮT BUỘC:
- Sinh test case theo các loại KHI CÓ CĂN CỨ từ yêu cầu: positive, negative, boundary,
  error_guessing, alternative_flow. KHÔNG bịa loại không có căn cứ.
- Mỗi test case gồm: title, type, preconditions, steps (mỗi step có action và expected),
  expected_result.
- KHÔNG tạo expected_result vượt quá phạm vi requirement đã duyệt.
- Bám actor/precondition/action/expected_outcome của requirement.
- KHÔNG gán ID (hệ thống tự gán).

Trả về JSON gồm: test_cases[].\
"""


class TestDesignAgent:
    def __init__(self, llm: LLMClient, model_name: str = "unknown"):
        self._llm = llm
        self._model_name = model_name

    def design(self, requirement: StructuredRequirement) -> TestDesignResult:
        if not requirement.action or not requirement.action.strip():
            return self._empty_result(requirement.id)

        user_prompt = self._build_user_prompt(requirement)
        draft = self._llm.structured_completion(SYSTEM_PROMPT, user_prompt, TestCaseDraft)

        cases = []
        links = []
        for index, tc in enumerate(draft.test_cases, start=1):
            tc_id = f"{requirement.id}-TC-{index:02d}"
            cases.append(tc.model_copy(update={"id": tc_id, "requirement_id": requirement.id}))
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
    def _build_user_prompt(requirement: StructuredRequirement) -> str:
        return (
            "Thiết kế test case cho yêu cầu đã duyệt dưới đây, trả JSON theo hướng dẫn.\n\n"
            f"- id: {requirement.id}\n"
            f"- title: {requirement.title}\n"
            f"- actor: {requirement.actor or '—'}\n"
            f"- precondition: {requirement.precondition or '—'}\n"
            f"- action: {requirement.action}\n"
            f"- expected_outcome: {requirement.expected_outcome or '—'}\n"
            f"- constraints: {', '.join(requirement.constraints) or '—'}"
        )
