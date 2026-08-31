"""Self-healing locator (đào sâu Repair Agent, mục 5.6 + 5.8).

Khi locator gãy lúc chạy, sinh locator thay thế cho ĐÚNG element có ý định ban đầu,
chấm điểm bằng locator_policy (ưu tiên UNIQUE + role>label>placeholder>text>test_id>css).

- `heal_action`: lõi THUẦN (test offline) — nhận candidates + count_fn, trả action đã chữa.
- `propose_candidates`: glue LIVE (integration) — scrape DOM sống sinh candidates.

Fail-closed: không có locator UNIQUE hợp lý -> None (không đề xuất bừa).
"""
from __future__ import annotations

import difflib

from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction
from src.services.locator_policy import choose_locator


def heal_action(failed_action: PlaywrightAction, candidates: list[dict], count_fn) -> PlaywrightAction | None:
    """candidates: [{strategy: LocatorStrategy, value, role_name?}]. count_fn(strategy, value, role_name)->int."""
    scored = []
    for c in candidates:
        strategy: LocatorStrategy = c["strategy"]
        value = c.get("value", "")
        role_name = c.get("role_name", "")
        matched = count_fn(strategy, value, role_name)
        if matched > 0:
            scored.append({"strategy": strategy.value, "value": value,
                           "role_name": role_name, "matched_count": matched})
    best = choose_locator(scored)
    if best is None or best["matched_count"] != 1:
        return None
    return failed_action.model_copy(update={
        "strategy": LocatorStrategy(best["strategy"]),
        "value": best["value"],
        "role_name": best.get("role_name", ""),
    })


def _descriptors(el, is_fill: bool) -> dict:
    return {
        "placeholder": el.get_attribute("placeholder"),
        "aria": el.get_attribute("aria-label"),
        "testid": el.get_attribute("data-test") or el.get_attribute("data-testid"),
        "id": el.get_attribute("id"),
        "name": el.get_attribute("name"),
        "text": "" if is_fill else (el.inner_text() or "").strip(),
    }


def _similarity(target: str, desc: dict) -> float:
    values = [v for v in desc.values() if v]
    return max((difflib.SequenceMatcher(None, target.lower(), v.lower()).ratio() for v in values), default=0.0)


def propose_candidates(page, failed_action: PlaywrightAction) -> list[dict]:
    """LIVE: chọn ĐÚNG element có ý định ban đầu (khớp mờ với locator lỗi) rồi sinh candidate đa strategy."""
    is_fill = failed_action.type == ActionType.FILL
    selector, role = ("input, textarea", "textbox") if is_fill else ("button, a, [role=button]", "button")
    target = failed_action.role_name or failed_action.value

    scored = [(el, _descriptors(el, is_fill)) for el in page.query_selector_all(selector)]
    if not scored:
        return []
    el, desc = max(scored, key=lambda ed: _similarity(target, ed[1])) if target else scored[0]
    acc_name = desc["aria"] or desc["placeholder"] or desc["text"]

    out: list[dict] = []
    if desc["placeholder"]:
        out.append({"strategy": LocatorStrategy.PLACEHOLDER, "value": desc["placeholder"]})
    if desc["aria"]:
        out.append({"strategy": LocatorStrategy.LABEL, "value": desc["aria"]})
    if acc_name:
        out.append({"strategy": LocatorStrategy.ROLE, "value": role, "role_name": acc_name})
    if desc["testid"]:
        out.append({"strategy": LocatorStrategy.TEST_ID, "value": desc["testid"]})
    if desc["text"]:
        out.append({"strategy": LocatorStrategy.TEXT, "value": desc["text"]})
    if desc["id"]:
        out.append({"strategy": LocatorStrategy.CSS, "value": f"#{desc['id']}"})
    elif desc["name"]:
        out.append({"strategy": LocatorStrategy.CSS, "value": f"[name='{desc['name']}']"})
    return out
