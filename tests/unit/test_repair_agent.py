"""Test Repair Agent (mock LLM) — gán đúng risk/outcome, không repair khi passed."""
from src.agents.repair_agent import RepairAgent
from src.models.playwright_artifacts import (
    ActionType, ExecStatus, ExecutionResult, LocatorStrategy, PlaywrightAction, PlaywrightPlan,
)
from src.models.repair import FailureType, RepairDraft, RepairOutcome, RiskLevel
from src.models.test_case import TestCase, TestType
from src.services.llm_client import MockLLMClient


def _old_plan():
    return PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.GOTO, arg="https://x/"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Usernamex", arg="u"),
        PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://x/inventory"),
    ])


def _fixed_plan():
    return PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.GOTO, arg="https://x/"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="u"),
        PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://x/inventory"),
    ])


def _failed_exec():
    return ExecutionResult(test_case_id="TC", status=ExecStatus.FAILED, exit_code=1,
                           stderr="TimeoutError: locator resolved to 0 elements", artifacts=["a.png"])


def _tc():
    return TestCase(id="TC", title="login", type=TestType.POSITIVE)


def test_propose_locator_fix_is_low_needs_approval():
    draft = RepairDraft(new_plan=_fixed_plan(), failure_type=FailureType.LOCATOR_NOT_FOUND, reason="sửa placeholder")
    prop = RepairAgent(MockLLMClient(draft), model_name="mock").propose(_old_plan(), _failed_exec(), _tc(), attempt=1)
    assert prop.risk_level == RiskLevel.LOW
    assert prop.requires_approval is True
    assert prop.outcome == RepairOutcome.PROPOSED
    assert prop.changed_kinds == ["locator_changed"]
    assert prop.diff and prop.evidence == ["a.png"]


def test_no_repair_when_passed():
    agent = RepairAgent(MockLLMClient(RepairDraft(new_plan=_fixed_plan())), model_name="mock")
    passed = ExecutionResult(test_case_id="TC", status=ExecStatus.PASSED, exit_code=0, stdout="PASSED")
    prop = agent.propose(_old_plan(), passed, _tc())
    assert prop.outcome == RepairOutcome.NOT_NEEDED and prop.requires_approval is False


def test_budget_exceeded_blocks():
    draft = RepairDraft(new_plan=_fixed_plan(), failure_type=FailureType.LOCATOR_NOT_FOUND)
    prop = RepairAgent(MockLLMClient(draft), model_name="mock").propose(_old_plan(), _failed_exec(), _tc(), attempt=3, budget=2)
    assert prop.outcome == RepairOutcome.BLOCKED_FOR_REVIEW


def test_propose_with_healing_low_needs_approval():
    # index 1 của _old_plan là FILL "Usernamex" -> chữa thành "Username" (chỉ đổi locator)
    healed = PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="u")
    prop = RepairAgent(model_name="det").propose_with_healing(_old_plan(), {1: healed}, _failed_exec(), _tc(), attempt=1)
    assert prop.risk_level == RiskLevel.LOW
    assert prop.requires_approval is True
    assert prop.outcome == RepairOutcome.PROPOSED
    assert prop.changed_kinds == ["locator_changed"]
    assert prop.diff and prop.evidence == ["a.png"]
