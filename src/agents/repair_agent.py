"""Repair Agent (architecture v0.1, mục 5.8) — constrained repair.

Đề xuất plan sửa (LLM) nhưng RỦI RO & gate do repair_policy (thuần) quyết định; agent KHÔNG
tự áp dụng đề xuất cần approval. Repair budget -> blocked_for_review.
"""
from __future__ import annotations

import difflib

from src.models.playwright_artifacts import ExecStatus, ExecutionResult, PlaywrightPlan
from src.models.repair import RepairDraft, RepairOutcome, RepairProposal
from src.models.test_case import TestCase
from src.services.llm_client import LLMClient
from src.services.repair_policy import classify_change, decide
from src.services.script_template import render_script

SYSTEM_PROMPT = """\
Bạn là kỹ sư sửa lỗi test tự động. Nhận một test Playwright THẤT BẠI cùng bằng chứng và plan
hiện tại; đề xuất plan sửa TỐI THIỂU để test chạy đúng.

QUY TẮC BẮT BUỘC:
- Ưu tiên sửa locator hoặc thêm chờ (low risk). KHÔNG xoá hoặc làm yếu assertion (expect_*)
  chỉ để test pass. KHÔNG đổi expected_result/URL kỳ vọng nếu không có căn cứ từ requirement.
- Giữ nguyên các action đúng; chỉ đổi cái gây lỗi.
- Phân loại failure_type và nêu lý do ngắn gọn.

Trả JSON RepairDraft: { "new_plan": {actions:[...]}, "failure_type": "...", "reason": "..." }.\
"""


def _plan_diff(old_plan: PlaywrightPlan, new_plan: PlaywrightPlan) -> str:
    old_code = render_script(old_plan).splitlines()
    new_code = render_script(new_plan).splitlines()
    return "\n".join(difflib.unified_diff(old_code, new_code, fromfile="old", tofile="new", lineterm=""))


class RepairAgent:
    def __init__(self, llm: LLMClient, model_name: str = "unknown"):
        self._llm = llm
        self._model_name = model_name

    def propose(self, old_plan: PlaywrightPlan, execution_result: ExecutionResult,
                test_case: TestCase, attempt: int = 1, budget: int = 2) -> RepairProposal:
        if execution_result.status == ExecStatus.PASSED:
            return RepairProposal(
                test_case_id=test_case.id, outcome=RepairOutcome.NOT_NEEDED,
                requires_approval=False, reason="Execution passed, không cần sửa.",
            )

        user_prompt = self._build_user_prompt(old_plan, execution_result, test_case)
        draft = self._llm.structured_completion(SYSTEM_PROMPT, user_prompt, RepairDraft)

        risk, semantic, kinds = classify_change(old_plan, draft.new_plan)
        outcome, requires_approval = decide(risk, attempt, budget)
        return RepairProposal(
            test_case_id=test_case.id,
            failure_type=draft.failure_type,
            risk_level=risk,
            semantic_impact=semantic,
            changed_kinds=kinds,
            diff=_plan_diff(old_plan, draft.new_plan),
            reason=draft.reason,
            evidence=execution_result.artifacts,
            requires_approval=requires_approval,
            outcome=outcome,
        )

    @staticmethod
    def _build_user_prompt(old_plan: PlaywrightPlan, execution_result: ExecutionResult, test_case: TestCase) -> str:
        return (
            f"Test case: {test_case.title}\n"
            f"Trạng thái: {execution_result.status.value} (exit {execution_result.exit_code})\n"
            f"stderr:\n{execution_result.stderr[-800:]}\n\n"
            f"Plan hiện tại (JSON):\n{old_plan.model_dump_json(indent=2)}\n\n"
            "Đề xuất plan sửa TỐI THIỂU. KHÔNG xoá/làm yếu assertion để test pass."
        )
