"""Test phân loại trạng thái execution (thuần, offline)."""
from src.agents.execution_agent import ExecutionAgent, classify_status
from src.models.playwright_artifacts import ExecStatus, GeneratedScript


def test_classify_passed():
    assert classify_status(0, "PASSED\n", "") == ExecStatus.PASSED


def test_classify_failed_on_assertion():
    assert classify_status(1, "", "AssertionError: locator resolved to 0 elements") == ExecStatus.FAILED


def test_classify_failed_on_timeout():
    assert classify_status(1, "", "playwright._impl._errors.TimeoutError: Timeout 30000ms") == ExecStatus.FAILED


def test_classify_error_otherwise():
    assert classify_status(1, "", "ModuleNotFoundError: No module named 'x'") == ExecStatus.ERROR


def test_execution_keeps_isolated_evidence_for_each_run(tmp_path):
    agent = ExecutionAgent()
    script = GeneratedScript(test_case_id="REQ 1/TC", code="print('PASSED')")
    first = agent.run(script, tmp_path)
    second = agent.run(script, tmp_path)
    assert first.status == second.status == ExecStatus.PASSED
    assert first.artifact_dir != second.artifact_dir
    for result in (first, second):
        assert any(path.endswith("generated_test.py") for path in result.artifacts)
        assert any(path.endswith("stdout.log") for path in result.artifacts)
        assert any(path.endswith("stderr.log") for path in result.artifacts)
