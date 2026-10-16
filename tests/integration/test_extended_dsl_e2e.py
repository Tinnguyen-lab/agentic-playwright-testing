"""E2E regression for every extended action and assertion in the safe DSL."""
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.agents.execution_agent import ExecutionAgent
from src.agents.playwright_generation_agent import ground_flow
from src.models.playwright_artifacts import (
    ActionType, ExecStatus, GeneratedScript, LocatorStrategy, PlaywrightAction, PlaywrightPlan,
)
from src.services.script_template import render_script


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"
PAGE_URL = (FIXTURE_DIR / "extended_dsl.html").as_uri()
UPLOAD_FILE = (FIXTURE_DIR / "extended_dsl_upload.txt").resolve()


def _action(kind, value="", arg="", **extra):
    strategy = extra.pop("strategy", LocatorStrategy.TEST_ID)
    return PlaywrightAction(type=kind, strategy=strategy, value=value, arg=arg, **extra)


def extended_plan() -> PlaywrightPlan:
    return PlaywrightPlan(test_case_id="DSL-EXT-E2E-001", target_url=PAGE_URL, actions=[
        PlaywrightAction(type=ActionType.GOTO, arg=PAGE_URL),
        _action(ActionType.SELECT_OPTION, "country", "vn"),
        _action(ActionType.EXPECT_TEXT, "country-status", "Selected: Vietnam"),
        _action(ActionType.HOVER, "hover-zone"),
        _action(ActionType.EXPECT_TEXT, "hover-status", "Hovered"),
        _action(ActionType.FILL, "keyboard", "agentic"),
        _action(ActionType.PRESS, "keyboard", "Enter"),
        _action(ActionType.EXPECT_VALUE, "keyboard", "agentic"),
        _action(ActionType.EXPECT_TEXT, "key-status", "Submitted with Enter"),
        _action(ActionType.DBLCLICK, "double-click"),
        _action(ActionType.EXPECT_TEXT, "double-status", "Double clicked"),
        _action(ActionType.CHECK, "terms"),
        _action(ActionType.EXPECT_CHECKED, "terms"),
        _action(ActionType.EXPECT_ENABLED, "enabled-button"),
        _action(ActionType.UPLOAD_FILE, "upload", str(UPLOAD_FILE)),
        _action(ActionType.EXPECT_TEXT, "upload-status", "Uploaded: extended_dsl_upload.txt"),
        _action(ActionType.DRAG_TO, "drag-source", target_strategy=LocatorStrategy.TEST_ID,
                target_value="drag-target"),
        _action(ActionType.EXPECT_TEXT, "drag-target", "Dropped: drag-source"),
        _action(ActionType.EXPECT_COUNT, '[data-testid="items"] li', "2", strategy=LocatorStrategy.CSS),
    ])


def test_extended_dsl_grounds_and_executes_end_to_end(tmp_path):
    plan = extended_plan()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        records = ground_flow(page, plan.actions)
        browser.close()

    assert records
    assert all(record.ok for record in records), records
    assert {record.locator_part for record in records} == {"source", "target"}

    code = render_script(plan, upload_root=FIXTURE_DIR)
    result = ExecutionAgent().run(
        GeneratedScript(test_case_id=plan.test_case_id, code=code), tmp_path / "execution",
    )
    assert result.status == ExecStatus.PASSED, result.stderr
    assert Path(result.artifact_dir, "screenshot.png").is_file()
    assert Path(result.artifact_dir, "screenshot.zip").is_file()
