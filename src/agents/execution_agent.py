"""Execution Agent (architecture v0.1, mục 5.7).

Chạy script Playwright trong cấu hình khóa, thu evidence, phân loại trạng thái. Không sửa test.
"""
from __future__ import annotations

import ast
import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.models.playwright_artifacts import ExecStatus, ExecutionResult, GeneratedScript


def visible_browser_code(code: str) -> str:
    """Bật cửa sổ browser trong cả script đã lưu trước khi mẫu sinh mã được cập nhật.

    Chỉ thay lời gọi Playwright browser.launch; các bước và assertion được giữ nguyên.
    Tệp generated_test.py trong thư mục bằng chứng là đúng mã đã thực thi.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code  # Để tiến trình con ghi lỗi cú pháp vào stderr như trước.
    source = code.encode("utf-8")
    lines = code.splitlines(keepends=True)
    line_starts = [0]
    for line in lines:
        line_starts.append(line_starts[-1] + len(line.encode("utf-8")))

    replacements: list[tuple[int, int, bytes]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        browser = node.func.value
        if node.func.attr != "launch" or not isinstance(browser, ast.Attribute):
            continue
        if browser.attr not in {"chromium", "firefox", "webkit"}:
            continue
        headless = next((kw for kw in node.keywords if kw.arg == "headless"), None)
        if headless is not None and isinstance(headless.value, ast.Constant) and headless.value.value is False:
            continue
        if headless is None:
            node.keywords.insert(0, ast.keyword(arg="headless", value=ast.Constant(value=False)))
        else:
            headless.value = ast.Constant(value=False)
        start = line_starts[node.lineno - 1] + node.col_offset
        end = line_starts[node.end_lineno - 1] + node.end_col_offset
        replacements.append((start, end, ast.unparse(node).encode("utf-8")))

    for start, end, replacement in sorted(replacements, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source.decode("utf-8")


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
        script_path.write_text(visible_browser_code(script.code), encoding="utf-8")

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
