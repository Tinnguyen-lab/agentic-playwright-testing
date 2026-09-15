"""Test render script Playwright từ PlaywrightPlan (thuần, offline)."""
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
