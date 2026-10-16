"""Reviewable impact/urgency estimates for test-case ordering.

Priority answers what to review/run first; severity estimates the impact if the
behavior fails. Neither value is an observed defect or a test result.
"""
from __future__ import annotations

from src.models.test_case import TestCase, TestPriority, TestSeverity, TestType

_PRIORITY_ORDER = {value: index for index, value in enumerate(TestPriority)}
_SEVERITY_ORDER = {value: index for index, value in enumerate(TestSeverity)}

_CRITICAL = ("mất dữ liệu", "data loss", "rò rỉ", "data breach", "unauthorized access",
             "truy cập trái phép", "thanh toán sai", "incorrect payment")
_HIGH = ("đăng nhập", "login", "authentication", "xác thực", "thanh toán", "payment",
         "checkout", "đặt hàng", "save", "lưu thông tin", "cập nhật", "update")


def evaluate_test_case(case: TestCase) -> TestCase:
    """Preserve a complete LLM/human estimate, otherwise apply conservative rules."""
    if case.priority is not None and case.severity is not None and case.triage_reason.strip():
        source = case.triage_source or "llm"
        return case.model_copy(update={"triage_source": source})

    text = " ".join((case.title, case.expected_result, case.source_excerpt,
                     " ".join(step.action for step in case.steps))).casefold()
    has_oracle = bool(case.expected_result.strip())
    if any(term in text for term in _CRITICAL):
        severity = TestSeverity.CRITICAL
        priority = TestPriority.P0 if has_oracle else TestPriority.P1
        basis = "nguy cơ mất dữ liệu, truy cập trái phép hoặc sai lệch thanh toán"
    elif any(term in text for term in _HIGH):
        severity = TestSeverity.HIGH
        priority = TestPriority.P1 if has_oracle else TestPriority.P2
        basis = "luồng nghiệp vụ chính hoặc xác thực/cập nhật dữ liệu"
    elif case.type == TestType.EXPLORATORY:
        severity = TestSeverity.LOW
        priority = TestPriority.P3
        basis = "khám phá UI/UX chưa có tác động nghiệp vụ được chứng minh"
    else:
        severity = TestSeverity.MEDIUM
        priority = TestPriority.P2 if has_oracle else TestPriority.P3
        basis = "tác động chưa được mô tả rõ trong yêu cầu"
    reason = f"Ước lượng theo quy tắc: {basis}; {'có' if has_oracle else 'chưa có'} oracle xác nhận."
    return case.model_copy(update={"priority": priority, "severity": severity,
                                   "triage_reason": reason, "triage_source": "rule"})


def triage_sort_key(case: TestCase) -> tuple[int, int, str]:
    assessed = evaluate_test_case(case)
    return (_PRIORITY_ORDER[assessed.priority], _SEVERITY_ORDER[assessed.severity], assessed.id)
