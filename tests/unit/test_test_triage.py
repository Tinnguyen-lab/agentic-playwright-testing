from src.models.test_case import TestCase, TestPriority, TestSeverity, TestType
from src.services.test_triage import evaluate_test_case, triage_sort_key


def test_login_flow_is_ranked_above_unscoped_exploration():
    login = evaluate_test_case(TestCase(id="TC-02", title="Đăng nhập hợp lệ", type=TestType.POSITIVE,
                                       expected_result="Dashboard hiển thị"))
    exploration = evaluate_test_case(TestCase(id="TC-01", title="Khám phá bố cục", type=TestType.EXPLORATORY))
    assert (login.priority, login.severity) == (TestPriority.P1, TestSeverity.HIGH)
    assert (exploration.priority, exploration.severity) == (TestPriority.P3, TestSeverity.LOW)
    assert sorted([exploration, login], key=triage_sort_key) == [login, exploration]


def test_complete_llm_triage_is_preserved():
    case = TestCase(id="T", title="UI", type=TestType.EXPLORATORY,
                    priority=TestPriority.P2, severity=TestSeverity.MEDIUM,
                    triage_reason="Common user journey")
    assessed = evaluate_test_case(case)
    assert assessed.priority == TestPriority.P2
    assert assessed.triage_source == "llm"


def test_legacy_case_without_rank_gets_reviewable_estimate():
    legacy = TestCase.model_validate({"id": "T", "title": "Checkout", "type": "positive",
                                      "expected_result": "Order placed"})
    assessed = evaluate_test_case(legacy)
    assert assessed.priority == TestPriority.P1
    assert assessed.triage_source == "rule" and assessed.triage_reason
