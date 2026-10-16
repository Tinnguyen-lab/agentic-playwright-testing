"""Lỗi từ tiến trình browser không được biến thành kết quả grounding rỗng."""
import subprocess

import pytest

from src.services.browser_tasks import BrowserTaskError, run_task


def test_run_task_handles_missing_stderr(monkeypatch):
    def failed_process(*args, **kwargs):
        assert kwargs["encoding"] == "utf-8"
        assert kwargs["errors"] == "replace"
        assert kwargs["env"]["PYTHONUTF8"] == "1"
        return subprocess.CompletedProcess(args[0], 1, stdout=None, stderr=None)

    monkeypatch.setattr("src.services.browser_tasks.subprocess.run", failed_process)
    with pytest.raises(BrowserTaskError, match="exit 1"):
        run_task("ground", {"plan": {"actions": []}})


def test_run_task_surfaces_playwright_error_line(monkeypatch):
    stderr = (
        "Traceback (most recent call last):\n"
        "playwright._impl._errors.Error: Page.goto: net::ERR_CONNECTION_REFUSED\n"
        "Call log:\n  - navigating to target\n"
    )
    monkeypatch.setattr(
        "src.services.browser_tasks.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, stdout="", stderr=stderr),
    )
    with pytest.raises(BrowserTaskError, match="ERR_CONNECTION_REFUSED"):
        run_task("snapshot", {"url": "http://127.0.0.1:5100/login"})
