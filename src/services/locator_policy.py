"""Chọn locator theo best practice Playwright (architecture v0.1, mục 5.6).

Ưu tiên role > label > placeholder > text > test_id > css; ưu tiên locator UNIQUE (khớp đúng 1).
"""
from __future__ import annotations

from src.models.playwright_artifacts import LocatorStrategy

PRIORITY = [
    LocatorStrategy.ROLE,
    LocatorStrategy.LABEL,
    LocatorStrategy.PLACEHOLDER,
    LocatorStrategy.TEXT,
    LocatorStrategy.TEST_ID,
    LocatorStrategy.CSS,
]


def choose_locator(candidates: list[dict]) -> dict | None:
    """candidates: [{strategy, value, matched_count}]. Chọn khớp-đúng-1 ưu tiên cao nhất;
    nếu không có cái nào unique thì chọn theo ưu tiên trong số còn lại (sẽ bị gắn cờ)."""
    unique = [c for c in candidates if c["matched_count"] == 1]
    pool = unique or candidates
    if not pool:
        return None
    return min(pool, key=lambda c: PRIORITY.index(LocatorStrategy(c["strategy"])))
