"""Test locator policy (thuần, offline)."""
from src.services.locator_policy import choose_locator


def test_prefers_unique_high_priority():
    cands = [
        {"strategy": "css", "value": "#user-name", "matched_count": 1},
        {"strategy": "placeholder", "value": "Username", "matched_count": 1},
        {"strategy": "role", "value": "textbox", "matched_count": 0},  # không tìm thấy
    ]
    best = choose_locator(cands)
    assert best["strategy"] == "placeholder"  # unique + ưu tiên hơn css; role bị loại vì count 0


def test_falls_back_by_priority_when_none_unique():
    cands = [
        {"strategy": "text", "value": "Login", "matched_count": 2},
        {"strategy": "css", "value": ".btn", "matched_count": 3},
    ]
    assert choose_locator(cands)["strategy"] == "text"  # text ưu tiên hơn css


def test_empty_returns_none():
    assert choose_locator([]) is None
