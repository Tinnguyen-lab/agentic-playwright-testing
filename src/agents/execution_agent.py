"""Execution Agent (architecture v0.1, mục 5.7).

Chạy script Playwright trong cấu hình khóa, thu evidence, phân loại trạng thái. Không sửa test.
"""
from __future__ import annotations

import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.models.playwright_artifacts import ExecStatus, ExecutionResult, GeneratedScript


def classify_status(exit_code: int, stdout: str, stderr: str) -> ExecStatus:
    if exit_code == 0 and "PASSED" in stdout:
        return ExecStatus.PASSED
    if any(k in stderr for k in ("AssertionError", "TimeoutError", "expect(")):
        return ExecStatus.FAILED
    return ExecStatus.ERROR


class ExecutionAgent:
    def run(self, script: GeneratedScript, workdir: str | Path, timeout: int = 120) -> ExecutionResult:
        root = Path(workdir)
        safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", script.test_case_id).strip("._") or "test_case"
        run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}-{uuid4().hex[:8]}"
        workdir = root / safe_id / run_id
        workdir.mkdir(parents=True, exist_ok=False)
        script_path = workdir / "generated_test.py"
        script_path.write_text(script.code, encoding="utf-8")

        try:
            proc = subprocess.run(
                [sys.executable, script_path.name],
                capture_output=True, text=True, timeout=timeout, cwd=str(workdir),
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else (exc.stdout or b"").decode(errors="replace")
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else (exc.stderr or b"").decode(errors="replace")
            (workdir / "stdout.log").write_text(stdout, encoding="utf-8")
            (workdir / "stderr.log").write_text(stderr or "timeout", encoding="utf-8")
            return ExecutionResult(
                test_case_id=script.test_case_id, status=ExecStatus.BLOCKED,
                run_id=run_id, artifact_dir=str(workdir), exit_code=124, stderr="timeout",
                artifacts=sorted(str(p) for p in workdir.iterdir()),
            )

        (workdir / "stdout.log").write_text(proc.stdout, encoding="utf-8")
        (workdir / "stderr.log").write_text(proc.stderr, encoding="utf-8")
        artifacts = sorted(str(p) for p in workdir.iterdir())
        return ExecutionResult(
            test_case_id=script.test_case_id,
            status=classify_status(proc.returncode, proc.stdout, proc.stderr),
            run_id=run_id, artifact_dir=str(workdir),
            exit_code=proc.returncode,
            stdout=proc.stdout[-2000:],
            stderr=proc.stderr[-2000:],
            artifacts=artifacts,
        )
