"""Test phân loại trạng thái execution (thuần, offline)."""
import subprocess
import json

from src.agents.execution_agent import ExecutionAgent, classify_status, visible_browser_code
from src.models.playwright_artifacts import ExecStatus, GeneratedScript


def test_classify_passed():
    assert classify_status(0, "PASSED\n", "") == ExecStatus.PASSED


def test_classify_failed_on_assertion():
    assert classify_status(1, "", "AssertionError: locator resolved to 0 elements") == ExecStatus.FAILED


def test_classify_failed_on_timeout():
    assert classify_status(1, "", "playwright._impl._errors.TimeoutError: Timeout 30000ms") == ExecStatus.FAILED


def test_classify_error_otherwise():
    assert classify_status(1, "", "ModuleNotFoundError: No module named 'x'") == ExecStatus.ERROR


def test_execution_makes_saved_playwright_script_visible(tmp_path, monkeypatch):
    legacy = 'browser = p.chromium.launch(args=["--disable-http2"])\nprint("PASSED")\n'
    updated = visible_browser_code(legacy)
    assert 'p.chromium.launch(headless=False, args=[' in updated
    assert visible_browser_code(updated) == updated
    assert 'headless=False' in visible_browser_code('browser = p.chromium.launch(headless=True)')
    assert '--start-maximized' in updated and '--start-fullscreen' in updated
    assert 'no_viewport=True' in visible_browser_code('context = browser.new_context()')

    monkeypatch.setattr("src.agents.execution_agent.subprocess.run",
                        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "PASSED\n", ""))
    result = ExecutionAgent().run(GeneratedScript(test_case_id="old", code=legacy), tmp_path)
    assert result.status == ExecStatus.PASSED
    executed = (tmp_path / "old" / result.run_id / "generated_test.py").read_text(encoding="utf-8")
    assert executed == updated


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


def test_execution_promotes_auth_only_after_passed_run(tmp_path, monkeypatch):
    destination = tmp_path / "saved" / "auth.json"
    seen_env = []

    def fake_run(*args, **kwargs):
        env = kwargs["env"]
        seen_env.append(env)
        candidate = env["AGENTIC_AUTH_STATE_OUT"]
        with open(candidate, "w", encoding="utf-8") as output:
            json.dump({"cookies": [{"name": "session"}], "origins": []}, output)
        return subprocess.CompletedProcess(args[0], 0 if len(seen_env) == 1 else 1,
                                           "PASSED\n" if len(seen_env) == 1 else "", "failure")

    monkeypatch.setattr("src.agents.execution_agent.subprocess.run", fake_run)
    script = GeneratedScript(test_case_id="login", code="print('PASSED')")
    first = ExecutionAgent().run(script, tmp_path / "runs", auth_state_save=destination)
    assert first.auth_state_saved and destination.is_file()
    second = ExecutionAgent().run(script, tmp_path / "runs", auth_state_in=destination,
                                  auth_state_save=destination)
    assert not second.auth_state_saved
    assert seen_env[1]["AGENTIC_AUTH_STATE_IN"] == str(destination.resolve())
    assert destination.is_file()
