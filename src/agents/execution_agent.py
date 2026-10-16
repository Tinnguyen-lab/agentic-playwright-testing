"""Execution Agent (architecture v0.1, mục 5.7).

Chạy script Playwright trong cấu hình khóa, thu evidence, phân loại trạng thái. Không sửa test.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.models.playwright_artifacts import ExecStatus, ExecutionResult, GeneratedScript
from src.services.auth_state import promote_state


def visible_browser_code(code: str) -> str:
    """Bật cửa sổ toàn màn hình trong cả script đã lưu từ template cũ.

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
        changed = False
        owner = node.func.value
        if (node.func.attr == "launch" and isinstance(owner, ast.Attribute) and
                owner.attr in {"chromium", "firefox", "webkit"}):
            headless = next((kw for kw in node.keywords if kw.arg == "headless"), None)
            if headless is None:
                node.keywords.insert(0, ast.keyword(arg="headless", value=ast.Constant(value=False)))
                changed = True
            elif not isinstance(headless.value, ast.Constant) or headless.value.value is not False:
                headless.value = ast.Constant(value=False)
                changed = True
            flags = ("--start-maximized", "--start-fullscreen")
            args = next((kw for kw in node.keywords if kw.arg == "args"), None)
            if args is None:
                node.keywords.append(ast.keyword(arg="args", value=ast.List(
                    elts=[ast.Constant(value=flag) for flag in flags], ctx=ast.Load())))
                changed = True
            elif isinstance(args.value, (ast.List, ast.Tuple)):
                existing = {item.value for item in args.value.elts if isinstance(item, ast.Constant)}
                missing = [flag for flag in flags if flag not in existing]
                if missing:
                    args.value = ast.List(elts=[*args.value.elts, *(ast.Constant(value=flag) for flag in missing)],
                                          ctx=ast.Load())
                    changed = True
        elif (node.func.attr == "new_context" and isinstance(owner, ast.Name) and
              owner.id == "browser"):
            viewport = next((kw for kw in node.keywords if kw.arg == "no_viewport"), None)
            if viewport is None:
                node.keywords.append(ast.keyword(arg="no_viewport", value=ast.Constant(value=True)))
                changed = True
            elif not isinstance(viewport.value, ast.Constant) or viewport.value.value is not True:
                viewport.value = ast.Constant(value=True)
                changed = True
        if not changed:
            continue
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
    def run(self, script: GeneratedScript, workdir: str | Path, timeout: int = 120,
            auth_state_in: str | Path | None = None,
            auth_state_save: str | Path | None = None) -> ExecutionResult:
        root = Path(workdir)
        safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", script.test_case_id).strip("._") or "test_case"
        run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}-{uuid4().hex[:8]}"
        workdir = root / safe_id / run_id
        workdir.mkdir(parents=True, exist_ok=False)
        script_path = workdir / "generated_test.py"
        script_path.write_text(visible_browser_code(script.code), encoding="utf-8")
        child_env = os.environ.copy()
        child_env["PYTHONUTF8"] = "1"
        child_env.pop("AGENTIC_AUTH_STATE_IN", None)
        child_env.pop("AGENTIC_AUTH_STATE_OUT", None)
        if auth_state_in is not None:
            state_in = Path(auth_state_in).resolve()
            if not state_in.is_file():
                raise FileNotFoundError(f"Authentication state not found: {state_in}")
            child_env["AGENTIC_AUTH_STATE_IN"] = str(state_in)
        candidate = workdir / "_auth_state_candidate.json" if auth_state_save is not None else None
        if candidate is not None:
            child_env["AGENTIC_AUTH_STATE_OUT"] = str(candidate)

        try:
            proc = subprocess.run(
                [sys.executable, script_path.name],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout, cwd=str(workdir), env=child_env,
            )
        except subprocess.TimeoutExpired as exc:
            if candidate is not None:
                candidate.unlink(missing_ok=True)
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
        status = classify_status(proc.returncode, proc.stdout, proc.stderr)
        auth_saved = False
        if candidate is not None:
            if status == ExecStatus.PASSED:
                auth_saved = promote_state(candidate, Path(auth_state_save))
            else:
                candidate.unlink(missing_ok=True)
        artifacts = sorted(str(p) for p in workdir.iterdir())
        return ExecutionResult(
            test_case_id=script.test_case_id,
            status=status,
            run_id=run_id, artifact_dir=str(workdir),
            exit_code=proc.returncode,
            stdout=proc.stdout[-2000:],
            stderr=proc.stderr[-2000:],
            artifacts=artifacts,
            auth_state_saved=auth_saved,
        )
