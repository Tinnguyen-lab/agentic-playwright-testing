from run_rq2 import _failure_category


def test_failure_taxonomy_separates_locator_timeout_and_plan_errors():
    assert _failure_category("passed", "") == "passed"
    assert _failure_category("error", "plan: invalid JSON") == "plan_generation"
    assert _failure_category("failed", "strict mode violation: locator resolved to 3 elements") == "ambiguous_locator"
    assert _failure_category("failed", "TimeoutError: Locator.click") == "timeout"
