import pytest

from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction


def test_drag_requires_typed_target_locator():
    with pytest.raises(ValueError, match="target locator"):
        PlaywrightAction(type=ActionType.DRAG_TO, strategy=LocatorStrategy.TEST_ID, value="source")


def test_expect_count_requires_non_negative_integer():
    with pytest.raises(ValueError, match="non-negative integer"):
        PlaywrightAction(type=ActionType.EXPECT_COUNT, strategy=LocatorStrategy.CSS, value="li", arg="many")
    with pytest.raises(ValueError, match="non-negative integer"):
        PlaywrightAction(type=ActionType.EXPECT_COUNT, strategy=LocatorStrategy.CSS, value="li", arg="-1")
