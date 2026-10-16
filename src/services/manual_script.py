"""Validate reviewer-edited Playwright Python before creating a new script version.

This is a quality gate, not a Python sandbox. The local reviewer is trusted to
edit code; execution still requires the existing AG-08 approval gate.
"""
from __future__ import annotations

import ast

MANUAL_MARKER = "# MANUAL_OVERRIDE: reviewer-edited Playwright script\n"


def is_manual_script(code: str) -> bool:
    return code.startswith(MANUAL_MARKER)


def _is_main_guard(node: ast.AST) -> bool:
    return (isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and
            isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__" and
            len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq) and
            len(node.test.comparators) == 1 and isinstance(node.test.comparators[0], ast.Constant) and
            node.test.comparators[0].value == "__main__")


def _is_call(node: ast.AST, name: str) -> bool:
    return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and
            isinstance(node.value.func, ast.Name) and node.value.func.id == name)


def validate_manual_script(code: str) -> str:
    """Return tagged code, or reject edits likely to produce an unearned PASS."""
    normalized = code.replace("\r\n", "\n").strip() + "\n"
    if is_manual_script(normalized):
        normalized = normalized[len(MANUAL_MARKER):]
    try:
        tree = ast.parse(normalized)
    except SyntaxError as exc:
        raise ValueError(f"Mã Python sai cú pháp ở dòng {exc.lineno}: {exc.msg}") from exc

    run = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run"), None)
    main = next((node for node in tree.body if _is_main_guard(node)), None)
    if run is None or main is None or len(main.body) != 2 or not _is_call(main.body[0], "run"):
        raise ValueError("Giữ nguyên hàm run() và phần gọi run() ở cuối script.")
    passed = main.body[1]
    if (not _is_call(passed, "print") or len(passed.value.args) != 1 or
            not isinstance(passed.value.args[0], ast.Constant) or passed.value.args[0].value != "PASSED"):
        raise ValueError("Dòng PASSED chỉ được in sau khi run() hoàn tất.")
    if any(isinstance(node, ast.ExceptHandler) for node in ast.walk(run)):
        raise ValueError("Không được bắt và bỏ qua lỗi trong run(); assertion lỗi phải làm test thất bại.")
    calls = [node for node in ast.walk(run) if isinstance(node, ast.Call)]
    has_browser = any(isinstance(node.func, ast.Attribute) and node.func.attr == "launch" for node in calls)
    has_assertion = any(
        isinstance(node, ast.Assert) and not isinstance(node.test, ast.Constant) or
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
        node.func.attr.startswith("to_") and isinstance(node.func.value, ast.Call) and
        isinstance(node.func.value.func, ast.Name) and node.func.value.func.id == "expect"
        for node in ast.walk(run)
    )
    if not has_browser or not has_assertion:
        raise ValueError("Script phải mở Playwright browser và có ít nhất một assertion thực tế.")
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and
           node.func.id in {"exec", "eval", "compile", "__import__"} for node in ast.walk(tree)):
        raise ValueError("Script sửa tay không được dùng exec/eval/compile/__import__.")
    return MANUAL_MARKER + normalized
