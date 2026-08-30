"""Test Playwright Generation Agent (plan qua mock, grounding qua fake counter) — offline."""
from src.agents.playwright_generation_agent import PlaywrightGenerationAgent, ground_actions
from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction, PlaywrightPlan
from src.models.test_case import TestCase, TestType
from src.services.llm_client import MockLLMClient


def _plan() -> PlaywrightPlan:
    return PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.GOTO, arg="https://www.saucedemo.com/"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="standard_user"),
    ])


def test_plan_sets_ids():
    agent = PlaywrightGenerationAgent(MockLLMClient(_plan()), model_name="mock")
    plan = agent.plan(TestCase(id="REQ-001-TC-01", title="login", type=TestType.POSITIVE), "https://www.saucedemo.com/")
    assert plan.test_case_id == "REQ-001-TC-01"
    assert plan.target_url == "https://www.saucedemo.com/"
    assert plan.actions[0].type == ActionType.GOTO


def test_ground_actions_with_fake_counter():
    actions = [
        PlaywrightAction(type=ActionType.GOTO, arg="u"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="x"),
        PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.CSS, value=".missing"),
    ]
    recs = ground_actions(actions, lambda strategy, value, role_name: 1 if value == "Username" else 0)
    assert len(recs) == 2  # goto không có locator -> bỏ qua
    assert recs[0].ok is True and recs[0].matched_count == 1
    assert recs[1].ok is False and recs[1].matched_count == 0


def test_generate_offline_no_grounding():
    agent = PlaywrightGenerationAgent(MockLLMClient(_plan()), model_name="mock")
    script = agent.generate(TestCase(id="TC", title="x", type=TestType.POSITIVE), "https://www.saucedemo.com/")
    assert script.test_case_id == "TC"
    assert "sync_playwright" in script.code
    assert script.grounding == []
