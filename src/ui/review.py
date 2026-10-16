"""Helper thuần cho UI review (KHÔNG phụ thuộc streamlit) — để test offline.

Tách khỏi glue Streamlit ([app.py](app.py)) để logic duyệt kiểm thử được.
"""
from __future__ import annotations

from src.models.approval import ApprovalDecision, is_approved
from src.models.playwright_artifacts import ActionType, PlaywrightPlan
from src.models.test_case import TestCase, TestPriority, TestSeverity, TestStep

_EXPECT = {
    ActionType.EXPECT_URL, ActionType.EXPECT_VISIBLE, ActionType.EXPECT_TEXT,
    ActionType.EXPECT_VALUE, ActionType.EXPECT_CHECKED, ActionType.EXPECT_ENABLED,
    ActionType.EXPECT_COUNT,
}


def approved_requirement_ids(requirements, decisions: list[ApprovalDecision],
                             versions: dict[str, int] | None = None) -> list[str]:
    """ID các yêu cầu mà quyết định MỚI NHẤT là APPROVED (AG-01)."""
    return [r.id for r in requirements if is_approved(decisions, r.id, (versions or {}).get(r.id))]


def approved_test_case_ids(test_cases, decisions: list[ApprovalDecision],
                           versions: dict[str, int] | None = None) -> list[str]:
    """ID các test case đã duyệt (AG-02)."""
    return [tc.id for tc in test_cases if is_approved(decisions, tc.id, (versions or {}).get(tc.id))]


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


def edited_test_case(tc: TestCase, title: str, steps_text: str, expected: str,
                     priority: TestPriority | None = None, severity: TestSeverity | None = None,
                     triage_reason: str | None = None) -> TestCase | None:
    """Test case sau khi người dùng sửa trên UI; None nếu không đổi gì (không tạo version mới)."""
    steps = [TestStep(action=line.strip()) for line in steps_text.splitlines() if line.strip()]
    chosen_priority = priority or tc.priority
    chosen_severity = severity or tc.severity
    chosen_reason = tc.triage_reason if triage_reason is None else triage_reason.strip()
    triage_changed = (chosen_priority != tc.priority or chosen_severity != tc.severity or
                      chosen_reason != tc.triage_reason)
    new = tc.model_copy(update={
        "title": title.strip() or tc.title, "steps": steps, "expected_result": expected.strip(),
        "priority": chosen_priority, "severity": chosen_severity, "triage_reason": chosen_reason,
        "triage_source": "human" if triage_changed else tc.triage_source,
    })
    return None if new == tc else new
