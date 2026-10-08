"""Test render script Playwright từ PlaywrightPlan (thuần, offline)."""
import ast

from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction, PlaywrightPlan
from src.services.script_template import render_script


def _login_plan() -> PlaywrightPlan:
    return PlaywrightPlan(
        test_case_id="REQ-001-TC-01",
        target_url="https://www.saucedemo.com/",
        actions=[
            PlaywrightAction(type=ActionType.GOTO, arg="https://www.saucedemo.com/"),
            PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="standard_user"),
            PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Password", arg="secret_sauce"),
            PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button", role_name="Login"),
            PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://www.saucedemo.com/inventory.html"),
        ],
    )


def test_render_login_script():
    code = render_script(_login_plan(), screenshot="shot.png")
    assert 'page.goto("https://www.saucedemo.com/")' in code
    assert 'page.get_by_placeholder("Username").fill("standard_user")' in code
    assert 'page.get_by_role("button", name="Login").click()' in code
    assert 'expect(page).to_have_url("https://www.saucedemo.com/inventory.html")' in code
    assert "sync_playwright" in code and 'page.screenshot(path="shot.png")' in code


def test_render_expect_visible_and_text():
    plan = PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.EXPECT_VISIBLE, strategy=LocatorStrategy.CSS, value=".error"),
        PlaywrightAction(type=ActionType.EXPECT_TEXT, strategy=LocatorStrategy.TEST_ID, value="error", arg="Epic sadface"),
    ])
    code = render_script(plan)
    assert 'expect(page.locator(".error")).to_be_visible()' in code
    assert 'expect(page.get_by_test_id("error")).to_contain_text("Epic sadface")' in code


def test_llm_strings_are_escaped_not_injected():
    evil = 'x"); import os; os.system("calc'
    plan = PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.EXPECT_TEXT, strategy=LocatorStrategy.TEXT, value='"Welcome UserName!"', arg=evil),
        PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button"),
    ])
    code = render_script(plan)
    tree = ast.parse(code)  # trước đây: SyntaxError / chèn được mã
    assert [type(n).__name__ for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))] == ["ImportFrom"]
    assert 'get_by_text("\\"Welcome UserName!\\"")' in code
    assert 'page.get_by_role("button").click()' in code  # role_name rỗng -> không có name=, khớp grounding
