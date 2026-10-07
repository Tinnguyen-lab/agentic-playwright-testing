"""Tác vụ trình duyệt dùng chung: aria snapshot, grounding, dò bước hỏng + self-healing.

Gọi trực tiếp (harness có sẵn browser) hoặc qua tiến trình con bằng `run_task` — Streamlit trên Windows chạy
Playwright sync trong cùng tiến trình hay vướng event loop, tiến trình con thì không.

    python -m src.services.browser_tasks <task>   # đọc JSON payload từ stdin, in JSON kết quả
"""
from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.agents.playwright_generation_agent import build_locator, ground_flow, live_count_fn
from src.models.playwright_artifacts import ActionType, PlaywrightAction, PlaywrightPlan
from src.services.locator_healing import heal_action, propose_candidates

SNAPSHOT_CHARS = 4000
LAUNCH_ARGS = ["--disable-http2"]  # giống script_template


def snapshot(page, chars: int = SNAPSHOT_CHARS) -> str:
    try:
        return page.locator("body").aria_snapshot()[:chars]
    except Exception:
        return ""


def probe(browser, plan: PlaywrightPlan):
    """Chạy lại plan trên trang thật tới bước hỏng đầu tiên. Trả (page, chỉ số|None, ghi chú, snapshot).

    Page được để mở (ở đúng trạng thái lúc hỏng) để self-healing dò DOM; người gọi đóng `page.context`.
    """
    page = browser.new_context().new_page()
    idx, note = None, "replay không gặp lỗi"
    for i, a in enumerate(plan.actions):
        try:
            if a.type == ActionType.GOTO:
                page.goto(a.arg)
                continue
            if a.type == ActionType.EXPECT_URL:
                page.wait_for_load_state()
                if page.url.rstrip("/") != a.arg.rstrip("/"):
                    idx, note = i, f"URL thực tế: {page.url}"
                    break
                continue
            loc = build_locator(page, a.strategy, a.value, a.role_name, a.nth)
            with contextlib.suppress(Exception):
                loc.first.wait_for(state="attached", timeout=2000)
            n = loc.count()
            if n != 1:
                idx, note = i, f"locator {a.strategy.value}:{a.value}[{a.role_name}] khớp {n} phần tử"
                break
            if a.type == ActionType.FILL:
                loc.fill(a.arg)
            elif a.type == ActionType.CLICK:
                loc.click()
                page.wait_for_load_state()
            elif a.type == ActionType.EXPECT_TEXT and a.arg not in loc.inner_text():
                idx, note = i, f"văn bản thực tế: {loc.inner_text()!r}"
                break
            elif a.type == ActionType.EXPECT_VISIBLE and not loc.is_visible():
                idx, note = i, "phần tử không hiển thị"
                break
        except Exception as e:  # thao tác hỏng giữa chừng
            idx, note = i, f"{type(e).__name__}: {str(e)[:150]}"
            break
    return page, idx, note, snapshot(page)


def try_heal(page, plan: PlaywrightPlan, idx) -> dict[int, PlaywrightAction] | None:
    """Self-healing tất định cho fill/click tại bước hỏng; None nếu không có locator thay thế duy nhất."""
    if idx is None or plan.actions[idx].type not in (ActionType.FILL, ActionType.CLICK):
        return None
    healed = heal_action(plan.actions[idx], propose_candidates(page, plan.actions[idx]), live_count_fn(page))
    return {idx: healed} if healed is not None else None


def heal_all(browser, plan: PlaywrightPlan, max_rounds: int = 6):
    """Chữa theo lô: dò bước hỏng → chữa → dò lại trên plan đã chữa, tới khi hết lỗi chữa được.

    Trả (các action đã chữa theo chỉ số, ghi chú + snapshot tại bước hỏng cuối cùng). Một mutation đổi nhiều locator
    cùng lúc (vd đổi id cả 3 ô đăng nhập) được chữa trong MỘT đề xuất thay vì tốn nhiều lượt ngân sách.
    """
    healed: dict[int, PlaywrightAction] = {}
    current = plan
    note, snap = "", ""
    for _ in range(max_rounds):
        page, idx, note, snap = probe(browser, current)
        fix = try_heal(page, current, idx)
        page.context.close()
        if not fix:
            break
        healed |= fix
        current = current.model_copy(update={"actions": [fix.get(i, a) for i, a in enumerate(current.actions)]})
    return healed, f"{note}\n{snap}"


# ---------- chạy trong tiến trình con ----------
def _task(name: str, payload: dict) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=LAUNCH_ARGS)
        try:
            if name == "snapshot":
                page = browser.new_page()
                with contextlib.suppress(Exception):
                    page.goto(payload["url"], timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=8000)
                return {"snapshot": snapshot(page, payload.get("chars", 6000))}
            plan = PlaywrightPlan.model_validate(payload["plan"])
            if name == "ground":
                page = browser.new_page()
                records = ground_flow(page, plan.actions, snapshot_chars=payload.get("chars", SNAPSHOT_CHARS))
                return {"records": [r.model_dump() for r in records]}
            if name == "probe_heal":
                healed, evidence = heal_all(browser, plan)
                return {"evidence": evidence, "healed": {str(k): v.model_dump(mode="json") for k, v in healed.items()}}
            raise ValueError(f"task không hỗ trợ: {name}")
        finally:
            browser.close()


def run_task(name: str, payload: dict, timeout: int = 180) -> dict:
    """Gọi tác vụ trong tiến trình con; lỗi trả {"error": ...} thay vì ném (UI hiển thị được)."""
    proc = subprocess.run([sys.executable, "-m", "src.services.browser_tasks", name], input=json.dumps(payload),
                          capture_output=True, text=True, encoding="utf-8", timeout=timeout,
                          cwd=Path(__file__).resolve().parents[2])
    if proc.returncode != 0:
        return {"error": proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else f"exit {proc.returncode}"}
    return json.loads(proc.stdout)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    print(json.dumps(_task(sys.argv[1], json.loads(sys.stdin.read())), ensure_ascii=False))
