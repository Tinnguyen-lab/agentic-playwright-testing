"""Execution Agent (architecture v0.1, mục 5.7).

Chạy script Playwright trong cấu hình khóa, thu evidence, phân loại trạng thái. Không sửa test.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from src.models.playwright_artifacts import ExecStatus, ExecutionResult, GeneratedScript


def classify_status(exit_code: int, stdout: str, stderr: str) -> ExecStatus:
    if exit_code == 0 and "PASSED" in stdout:
        return ExecStatus.PASSED
    if any(k in stderr for k in ("AssertionError", "TimeoutError", "expect(")):
        return ExecStatus.FAILED
    return ExecStatus.ERROR


class ExecutionAgent:
    def run(self, script: GeneratedScript, workdir: str | Path, timeout: int = 120) -> ExecutionResult:
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        script_path = workdir / f"{script.test_case_id}.py"
        script_path.write_text(script.code, encoding="utf-8")

        try:
            proc = subprocess.run(
                [sys.executable, script_path.name],
                capture_output=True, text=True, timeout=timeout, cwd=str(workdir),
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                test_case_id=script.test_case_id, status=ExecStatus.BLOCKED,
                exit_code=124, stderr="timeout",
            )

        artifacts = sorted(str(p) for p in workdir.glob("*.png"))
        return ExecutionResult(
            test_case_id=script.test_case_id,
            status=classify_status(proc.returncode, proc.stdout, proc.stderr),
            exit_code=proc.returncode,
            stdout=proc.stdout[-2000:],
            stderr=proc.stderr[-2000:],
            artifacts=artifacts,
        )
