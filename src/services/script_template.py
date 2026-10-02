"""Sinh script Playwright Python (self-contained) từ PlaywrightPlan qua jinja2."""
from __future__ import annotations

import jinja2

from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightPlan

_SKELETON = jinja2.Template(
    """\
from playwright.sync_api import sync_playwright, expect


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        {{ body }}
        page.screenshot(path="{{ screenshot }}")
        browser.close()


if __name__ == "__main__":
    run()
    print("PASSED")
"""
)


def _locator_expr(action) -> str:
    s = action.strategy
    if s == LocatorStrategy.ROLE:
        return f'page.get_by_role("{action.value}", name="{action.role_name}")'
    if s == LocatorStrategy.LABEL:
        return f'page.get_by_label("{action.value}")'
    if s == LocatorStrategy.PLACEHOLDER:
        return f'page.get_by_placeholder("{action.value}")'
    if s == LocatorStrategy.TEXT:
        return f'page.get_by_text("{action.value}")'
    if s == LocatorStrategy.TEST_ID:
        return f'page.get_by_test_id("{action.value}")'
    return f'page.locator("{action.value}")'


def _action_line(action) -> str:
    t = action.type
    if t == ActionType.GOTO:
        return f'page.goto("{action.arg}")'
    if t == ActionType.FILL:
        return f'{_locator_expr(action)}.fill("{action.arg}")'
    if t == ActionType.CLICK:
        return f"{_locator_expr(action)}.click()"
    if t == ActionType.EXPECT_URL:
        return f'expect(page).to_have_url("{action.arg}")'
    if t == ActionType.EXPECT_VISIBLE:
        return f"expect({_locator_expr(action)}).to_be_visible()"
    if t == ActionType.EXPECT_TEXT:
        return f'expect({_locator_expr(action)}).to_contain_text("{action.arg}")'
    raise ValueError(f"action type không hỗ trợ: {action.type}")


def render_script(plan: PlaywrightPlan, screenshot: str = "screenshot.png") -> str:
    body = "\n        ".join(_action_line(a) for a in plan.actions)
    return _SKELETON.render(body=body, screenshot=screenshot)
