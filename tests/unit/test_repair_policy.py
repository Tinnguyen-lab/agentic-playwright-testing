"""Test repair policy (thuần, tất định) — cốt lõi constrained repair."""
from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction, PlaywrightPlan
from src.models.repair import RepairOutcome, RiskLevel
from src.services.repair_policy import classify_change, decide


def _login_actions():
    return [
        PlaywrightAction(type=ActionType.GOTO, arg="https://x/"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="u"),
        PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button", role_name="Login"),
        PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://x/inventory"),
    ]


def _plan(actions):
    return PlaywrightPlan(actions=actions)


def test_locator_change_is_low():
    acts = _login_actions()
    acts[1] = PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.CSS, value="#user-name", arg="u")
    risk, semantic, kinds = classify_change(_plan(_login_actions()), _plan(acts))
    assert risk == RiskLevel.LOW and semantic is False and kinds == ["locator_changed"]


def test_test_data_change_is_medium():
    acts = _login_actions()
    acts[1] = PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="other")
    risk, _, kinds = classify_change(_plan(_login_actions()), _plan(acts))
    assert risk == RiskLevel.MEDIUM and "test_data_changed" in kinds


def test_assertion_change_is_high_semantic():
    acts = _login_actions()
    acts[3] = PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://x/other")
    risk, semantic, kinds = classify_change(_plan(_login_actions()), _plan(acts))
    assert risk == RiskLevel.HIGH and semantic is True and "assertion_changed" in kinds


def test_step_removed_is_high():
    risk, semantic, kinds = classify_change(_plan(_login_actions()), _plan(_login_actions()[:-1]))
    assert risk == RiskLevel.HIGH and semantic is True and "step_removed" in kinds


def test_decide_gates():
    assert decide(RiskLevel.LOW, attempt=1) == (RepairOutcome.PROPOSED, True)
    assert decide(RiskLevel.LOW, attempt=3, budget=2)[0] == RepairOutcome.BLOCKED_FOR_REVIEW
    assert decide(RiskLevel.PROHIBITED, attempt=1)[0] == RepairOutcome.REFUSED
    assert decide(RiskLevel.HIGH, attempt=1)[1] is True
