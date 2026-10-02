"""Helper thuần cho UI review (KHÔNG phụ thuộc streamlit) — để test offline.

Tách khỏi glue Streamlit ([app.py](app.py)) để logic duyệt kiểm thử được.
"""
from __future__ import annotations

from src.models.approval import ApprovalDecision, is_approved


def approved_requirement_ids(requirements, decisions: list[ApprovalDecision]) -> list[str]:
    """ID các yêu cầu mà quyết định MỚI NHẤT là APPROVED (AG-01)."""
    return [r.id for r in requirements if is_approved(decisions, r.id)]


def approved_test_case_ids(test_cases, decisions: list[ApprovalDecision]) -> list[str]:
    """ID các test case đã duyệt (AG-02)."""
    return [tc.id for tc in test_cases if is_approved(decisions, tc.id)]
