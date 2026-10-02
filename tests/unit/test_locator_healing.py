"""Test self-healing locator (lõi thuần, offline)."""
from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction
from src.services.locator_healing import heal_action


def _fill(strategy, value):
    return PlaywrightAction(type=ActionType.FILL, strategy=strategy, value=value, arg="standard_user")


def test_pick_unique_placeholder_over_ambiguous_css():
    failed = _fill(LocatorStrategy.PLACEHOLDER, "Usernamex")
    candidates = [
        {"strategy": LocatorStrategy.PLACEHOLDER, "value": "Username"},
        {"strategy": LocatorStrategy.CSS, "value": "input"},  # khớp nhiều
    ]
    count = lambda s, v, r: 1 if s == LocatorStrategy.PLACEHOLDER else 3
    healed = heal_action(failed, candidates, count)
    assert healed is not None
    assert healed.strategy == LocatorStrategy.PLACEHOLDER and healed.value == "Username"
    assert healed.type == ActionType.FILL and healed.arg == "standard_user"  # giữ type + data


def test_role_unique_beats_css_unique():
    failed = _fill(LocatorStrategy.PLACEHOLDER, "Usernamex")
    candidates = [
        {"strategy": LocatorStrategy.CSS, "value": "#user-name"},
        {"strategy": LocatorStrategy.ROLE, "value": "textbox", "role_name": "Username"},
    ]
    healed = heal_action(failed, candidates, lambda s, v, r: 1)
    assert healed.strategy == LocatorStrategy.ROLE
    assert healed.value == "textbox" and healed.role_name == "Username"


def test_none_when_nothing_matches():
    failed = _fill(LocatorStrategy.PLACEHOLDER, "Usernamex")
    candidates = [{"strategy": LocatorStrategy.CSS, "value": "input"}]
    assert heal_action(failed, candidates, lambda s, v, r: 0) is None


def test_none_when_only_ambiguous():
    failed = _fill(LocatorStrategy.PLACEHOLDER, "Usernamex")
    candidates = [{"strategy": LocatorStrategy.CSS, "value": "input"}]
    assert heal_action(failed, candidates, lambda s, v, r: 3) is None  # có khớp nhưng không unique
