"""Repair policy — phân loại rủi ro của một đề xuất sửa và quyết định gate (mục 9).

Đây là phần cốt lõi của constrained repair: RỦI RO do POLICY (không phải LLM) quyết định,
dựa trên WHAT thay đổi giữa plan cũ và plan mới. Thuần, tất định, test kỹ.
"""
from __future__ import annotations

from src.models.playwright_artifacts import ActionType, PlaywrightPlan
from src.models.repair import RepairOutcome, RiskLevel

_EXPECT = {ActionType.EXPECT_URL, ActionType.EXPECT_VISIBLE, ActionType.EXPECT_TEXT}
_LOCATOR_ACTIONS = {ActionType.FILL, ActionType.CLICK, ActionType.EXPECT_VISIBLE, ActionType.EXPECT_TEXT}
_HIGH = {"assertion_changed", "action_type_changed", "step_removed"}
_MEDIUM = {"test_data_changed", "navigation_changed", "step_added"}


def _locator_tuple(action) -> tuple:
    return (action.strategy, action.value, action.role_name)


def classify_change(old_plan: PlaywrightPlan, new_plan: PlaywrightPlan) -> tuple[RiskLevel, bool, list[str]]:
    old, new = old_plan.actions, new_plan.actions
    kinds: set[str] = set()
    if len(new) < len(old):
        kinds.add("step_removed")
    if len(new) > len(old):
        kinds.add("step_added")

    for o, n in zip(old, new):
        if o.type != n.type:
            kinds.add("action_type_changed")
            continue
        if o.type in _EXPECT and (o.arg != n.arg or o.value != n.value or o.role_name != n.role_name):
            kinds.add("assertion_changed")
        if o.type == ActionType.FILL and o.arg != n.arg:
            kinds.add("test_data_changed")
        if o.type == ActionType.GOTO and o.arg != n.arg:
            kinds.add("navigation_changed")
        if o.type in _LOCATOR_ACTIONS and _locator_tuple(o) != _locator_tuple(n):
            kinds.add("locator_changed")

    if kinds & _HIGH:
        risk = RiskLevel.HIGH
    elif kinds & _MEDIUM:
        risk = RiskLevel.MEDIUM
    else:
        risk = RiskLevel.LOW  # chỉ đổi locator hoặc không đổi gì đáng kể
    semantic = bool(kinds & {"assertion_changed", "action_type_changed", "step_removed"})
    return risk, semantic, sorted(kinds)


def decide(risk: RiskLevel, attempt: int, budget: int = 2) -> tuple[RepairOutcome, bool]:
    """Quyết định outcome + requires_approval. Mọi mức đều CẦN người duyệt (không tự áp dụng)."""
    if risk == RiskLevel.PROHIBITED:
        return RepairOutcome.REFUSED, True
    if attempt > budget:
        return RepairOutcome.BLOCKED_FOR_REVIEW, True
    return RepairOutcome.PROPOSED, True
