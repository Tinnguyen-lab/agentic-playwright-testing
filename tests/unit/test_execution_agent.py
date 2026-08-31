"""Test phân loại trạng thái execution (thuần, offline)."""
from src.agents.execution_agent import classify_status
from src.models.playwright_artifacts import ExecStatus


def test_classify_passed():
    assert classify_status(0, "PASSED\n", "") == ExecStatus.PASSED


def test_classify_failed_on_assertion():
    assert classify_status(1, "", "AssertionError: locator resolved to 0 elements") == ExecStatus.FAILED


def test_classify_failed_on_timeout():
    assert classify_status(1, "", "playwright._impl._errors.TimeoutError: Timeout 30000ms") == ExecStatus.FAILED


def test_classify_error_otherwise():
    assert classify_status(1, "", "ModuleNotFoundError: No module named 'x'") == ExecStatus.ERROR
