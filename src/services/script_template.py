"""Sinh script Playwright Python (self-contained) từ PlaywrightPlan qua jinja2."""
from __future__ import annotations

import json
from pathlib import Path

import jinja2

from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightPlan

_SKELETON = jinja2.Template(
    """\
from playwright.sync_api import sync_playwright, expect
from pathlib import Path

_UPLOAD_ROOT = Path({{ upload_root }}).resolve()

def _safe_upload_path(value):
    path = Path(value).resolve()
    if path != _UPLOAD_ROOT and _UPLOAD_ROOT not in path.parents:
        raise ValueError(f"upload_file must stay under approved test-data root: {_UPLOAD_ROOT}")
    if not path.is_file():
        raise FileNotFoundError(f"upload_file not found: {path}")
    return str(path)

expect.set_options(timeout=10_000)  # trang demo có phần tử chờ ~5s (dynamic_loading)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-http2"])  # mở cửa sổ để người dùng theo dõi
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.set_default_timeout(10_000)  # thao tác (click/fill); điều hướng giữ 30s
        page.set_default_navigation_timeout(30_000)
        try:
            {{ body }}
        finally:
            page.screenshot(path={{ screenshot }})
            context.tracing.stop(path={{ trace }})
            browser.close()


if __name__ == "__main__":
    run()
    print("PASSED")
"""
)


def _lit(value) -> str:
    """Chuỗi do LLM/người dùng sinh -> literal Python an toàn (escape dấu nháy, backslash, xuống dòng).

    Chèn thẳng "{value}" thì giá trị có dấu nháy làm hỏng cú pháp, tệ hơn là cho phép chèn mã vào script sẽ được chạy.
    """
    return json.dumps(value or "", ensure_ascii=False)


def _locator_expr(action) -> str:
    base = _base_locator_expr(action)
    return f"{base}.nth({action.nth})" if action.nth >= 0 else base


def _target_locator_expr(action) -> str:
    class Target:
        strategy = action.target_strategy
        value = action.target_value
        role_name = action.target_role_name
        nth = action.target_nth
    return _locator_expr(Target())


def _base_locator_expr(action) -> str:
    s = action.strategy
    if s == LocatorStrategy.ROLE:
        name = f", name={_lit(action.role_name)}" if action.role_name else ""  # khớp build_locator khi grounding
        return f"page.get_by_role({_lit(action.value)}{name})"
    if s == LocatorStrategy.LABEL:
        return f'page.get_by_label({_lit(action.value)})'
    if s == LocatorStrategy.PLACEHOLDER:
        return f'page.get_by_placeholder({_lit(action.value)})'
    if s == LocatorStrategy.TEXT:
        return f'page.get_by_text({_lit(action.value)})'
    if s == LocatorStrategy.TEST_ID:
        return f'page.get_by_test_id({_lit(action.value)})'
    return f'page.locator({_lit(action.value)})'


def _action_line(action) -> str:
    t = action.type
    if t == ActionType.GOTO:
        return f'page.goto({_lit(action.arg)})'
    if t == ActionType.FILL:
        return f'{_locator_expr(action)}.fill({_lit(action.arg)})'
    if t == ActionType.CLICK:
        return f"{_locator_expr(action)}.click()"
    if t == ActionType.SELECT_OPTION:
        return f"{_locator_expr(action)}.select_option({_lit(action.arg)})"
    if t == ActionType.CHECK:
        return f"{_locator_expr(action)}.check()"
    if t == ActionType.UNCHECK:
        return f"{_locator_expr(action)}.uncheck()"
    if t == ActionType.PRESS:
        return f"{_locator_expr(action)}.press({_lit(action.arg)})"
    if t == ActionType.HOVER:
        return f"{_locator_expr(action)}.hover()"
    if t == ActionType.DBLCLICK:
        return f"{_locator_expr(action)}.dblclick()"
    if t == ActionType.UPLOAD_FILE:
        return f"{_locator_expr(action)}.set_input_files(_safe_upload_path({_lit(action.arg)}))"
    if t == ActionType.DRAG_TO:
        if action.target_strategy is None:
            raise ValueError("drag_to requires target_strategy")
        return f"{_locator_expr(action)}.drag_to({_target_locator_expr(action)})"
    if t == ActionType.EXPECT_URL:
        return f'expect(page).to_have_url({_lit(action.arg)})'
    if t == ActionType.EXPECT_VISIBLE:
        return f"expect({_locator_expr(action)}).to_be_visible()"
    if t == ActionType.EXPECT_TEXT:
        return f'expect({_locator_expr(action)}).to_contain_text({_lit(action.arg)})'
    if t == ActionType.EXPECT_VALUE:
        return f"expect({_locator_expr(action)}).to_have_value({_lit(action.arg)})"
    if t == ActionType.EXPECT_CHECKED:
        return f"expect({_locator_expr(action)}).to_be_checked()"
    if t == ActionType.EXPECT_ENABLED:
        return f"expect({_locator_expr(action)}).to_be_enabled()"
    if t == ActionType.EXPECT_COUNT:
        try:
            count = int(action.arg)
        except (TypeError, ValueError) as exc:
            raise ValueError("expect_count requires an integer arg") from exc
        return f"expect({_locator_expr(action)}).to_have_count({count})"
    raise ValueError(f"action type không hỗ trợ: {action.type}")


def render_script(plan: PlaywrightPlan, screenshot: str = "screenshot.png",
                  upload_root: str | Path | None = None) -> str:
    body = "\n            ".join(_action_line(a) for a in plan.actions)
    trace = str(Path(screenshot).with_suffix(".zip"))
    root = Path(upload_root or Path.cwd()).resolve()
    return _SKELETON.render(body=body, screenshot=_lit(screenshot), trace=_lit(trace),
                            upload_root=_lit(str(root)))
