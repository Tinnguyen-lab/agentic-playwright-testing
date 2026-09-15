"""Repair Agent (architecture v0.1, mục 5.8) — constrained repair.

Đề xuất plan sửa (LLM) nhưng RỦI RO & gate do repair_policy (thuần) quyết định; agent KHÔNG
tự áp dụng đề xuất cần approval. Repair budget -> blocked_for_review.
"""
from __future__ import annotations

import difflib

from src.models.playwright_artifacts import ExecStatus, ExecutionResult, PlaywrightAction, PlaywrightPlan
from src.models.repair import FailureType, RepairDraft, RepairOutcome, RepairProposal
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


def _loc(action: PlaywrightAction) -> str:
    strategy = action.strategy.value if action.strategy else "?"
    label = f"{action.value}[{action.role_name}]" if action.value and action.role_name else (action.value or action.role_name)
    return f"{strategy}:{label}"


def _plan_diff(old_plan: PlaywrightPlan, new_plan: PlaywrightPlan) -> str:
    old_code = render_script(old_plan).splitlines()
    new_code = render_script(new_plan).splitlines()
    return "\n".join(difflib.unified_diff(old_code, new_code, fromfile="old", tofile="new", lineterm=""))


class RepairAgent:
    def __init__(self, llm: LLMClient | None = None, model_name: str = "unknown"):
        self._llm = llm
        self._model_name = model_name

    def propose(self, old_plan: PlaywrightPlan, execution_result: ExecutionResult,
                test_case: TestCase, attempt: int = 1, budget: int = 2) -> RepairProposal:
        not_needed = self._not_needed_if_passed(execution_result, test_case)
        if not_needed is not None:
            return not_needed

        user_prompt = self._build_user_prompt(old_plan, execution_result, test_case)
        draft = self._llm.structured_completion(SYSTEM_PROMPT, user_prompt, RepairDraft)
        return self._build_proposal(old_plan, draft.new_plan, draft.failure_type, draft.reason,
                                    execution_result, test_case, attempt, budget)

    def propose_with_healing(self, old_plan: PlaywrightPlan, healed_actions: dict[int, PlaywrightAction],
                             execution_result: ExecutionResult, test_case: TestCase,
                             attempt: int = 1, budget: int = 2) -> RepairProposal:
        """Đường TẤT ĐỊNH (không LLM): thay các action đã tự-chữa vào plan cũ rồi qua policy + gate."""
        not_needed = self._not_needed_if_passed(execution_result, test_case)
        if not_needed is not None:
            return not_needed

        actions = list(old_plan.actions)
        changes = []
        for index, healed in healed_actions.items():
            old = actions[index]
            changes.append(f"{_loc(old)} -> {_loc(healed)}")
            actions[index] = healed
        new_plan = old_plan.model_copy(update={"actions": actions})
        reason = "Self-healing locator từ DOM sống: " + "; ".join(changes)
        return self._build_proposal(old_plan, new_plan, FailureType.LOCATOR_NOT_FOUND, reason,
                                    execution_result, test_case, attempt, budget)

    @staticmethod
    def _not_needed_if_passed(execution_result: ExecutionResult, test_case: TestCase) -> RepairProposal | None:
        if execution_result.status == ExecStatus.PASSED:
            return RepairProposal(
                test_case_id=test_case.id, outcome=RepairOutcome.NOT_NEEDED,
                requires_approval=False, reason="Execution passed, không cần sửa.",
            )
        return None

    @staticmethod
    def _build_proposal(old_plan: PlaywrightPlan, new_plan: PlaywrightPlan, failure_type: FailureType,
                        reason: str, execution_result: ExecutionResult, test_case: TestCase,
                        attempt: int, budget: int) -> RepairProposal:
        risk, semantic, kinds = classify_change(old_plan, new_plan)
        outcome, requires_approval = decide(risk, attempt, budget)
        return RepairProposal(
            test_case_id=test_case.id,
            failure_type=failure_type,
            risk_level=risk,
            semantic_impact=semantic,
            changed_kinds=kinds,
            diff=_plan_diff(old_plan, new_plan),
            reason=reason,
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
