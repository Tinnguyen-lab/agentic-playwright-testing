"""Helper thuần cho UI review (KHÔNG phụ thuộc streamlit) — để test offline.

Tách khỏi glue Streamlit ([app.py](app.py)) để logic duyệt kiểm thử được.
"""
from __future__ import annotations

from src.models.approval import ApprovalDecision, is_approved
from src.models.playwright_artifacts import ActionType, PlaywrightPlan
from src.models.test_case import TestCase, TestStep

_EXPECT = {ActionType.EXPECT_URL, ActionType.EXPECT_VISIBLE, ActionType.EXPECT_TEXT}


def approved_requirement_ids(requirements, decisions: list[ApprovalDecision]) -> list[str]:
    """ID các yêu cầu mà quyết định MỚI NHẤT là APPROVED (AG-01)."""
    return [r.id for r in requirements if is_approved(decisions, r.id)]


def approved_test_case_ids(test_cases, decisions: list[ApprovalDecision]) -> list[str]:
    """ID các test case đã duyệt (AG-02)."""
    return [tc.id for tc in test_cases if is_approved(decisions, tc.id)]


def repair_gate(old: PlaywrightPlan, new: PlaywrightPlan, changed_kinds: list[str]) -> str:
    """Cổng duyệt cho một đề xuất sửa (architecture v0.1, mục 8).

    AG-05: bỏ/thêm/đổi loại bước hoặc đổi dữ liệu, điều hướng · AG-04: đổi giá trị kỳ vọng của assertion (oracle)
    · AG-03: đổi phần tử mà assertion kiểm · REPAIR-LOW: chỉ đổi locator của thao tác (vẫn cần người bấm duyệt).
    """
    kinds = set(changed_kinds)
    if kinds & {"step_removed", "step_added", "action_type_changed", "test_data_changed", "navigation_changed"}:
        return "AG-05"
    if "assertion_changed" in kinds:
        pairs = [(o, n) for o, n in zip(old.actions, new.actions) if o.type in _EXPECT]
        return "AG-04" if any(o.arg != n.arg for o, n in pairs) else "AG-03"
    return "REPAIR-LOW"


def edited_test_case(tc: TestCase, title: str, steps_text: str, expected: str) -> TestCase | None:
    """Test case sau khi người dùng sửa trên UI; None nếu không đổi gì (không tạo version mới)."""
    steps = [TestStep(action=line.strip()) for line in steps_text.splitlines() if line.strip()]
    new = tc.model_copy(update={"title": title.strip() or tc.title, "steps": steps, "expected_result": expected.strip()})
    return None if new == tc else new
