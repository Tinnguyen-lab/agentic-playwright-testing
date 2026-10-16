"""Tác vụ trình duyệt dùng chung: aria snapshot, grounding, dò bước hỏng + self-healing.

Gọi trực tiếp (harness có sẵn browser) hoặc qua tiến trình con bằng `run_task` — Streamlit trên Windows chạy
Playwright sync trong cùng tiến trình hay vướng event loop, tiến trình con thì không.

    python -m src.services.browser_tasks <task>   # đọc JSON payload từ stdin, in JSON kết quả
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.agents.playwright_generation_agent import _grounding_ok, build_locator, ground_flow, live_count_fn
from src.models.playwright_artifacts import ActionType, PlaywrightAction, PlaywrightPlan
from src.services.locator_healing import heal_action, propose_candidates

SNAPSHOT_CHARS = 4000
LAUNCH_ARGS = ["--disable-http2"]  # giống script_template


class BrowserTaskError(RuntimeError):
    """Tác vụ trình duyệt thất bại; UI có thể hiển thị thông báo ngắn gọn."""


def snapshot(page, chars: int = SNAPSHOT_CHARS) -> str:
    try:
        return page.locator("body").aria_snapshot()[:chars]
    except Exception:
        return ""


def probe(browser, plan: PlaywrightPlan, storage_state: str | None = None):
    """Chạy lại plan trên trang thật tới bước hỏng đầu tiên. Trả (page, chỉ số|None, ghi chú, snapshot).

    Page được để mở (ở đúng trạng thái lúc hỏng) để self-healing dò DOM; người gọi đóng `page.context`.
    """
    context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
    page = context.new_page()
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
            if not _grounding_ok(a, n):
                idx, note = i, f"locator {a.strategy.value}:{a.value}[{a.role_name}] khớp {n} phần tử"
                break
            target = None
            if a.type == ActionType.DRAG_TO:
                if a.target_strategy is None:
                    idx, note = i, "drag_to missing target locator"
                    break
                target = build_locator(page, a.target_strategy, a.target_value, a.target_role_name, a.target_nth)
                if target.count() != 1:
                    idx, note = i, f"drag target matched {target.count()} elements"
                    break
            if a.type == ActionType.FILL:
                loc.fill(a.arg)
            elif a.type == ActionType.CLICK:
                loc.click()
                page.wait_for_load_state()
            elif a.type == ActionType.SELECT_OPTION:
                loc.select_option(a.arg)
            elif a.type == ActionType.CHECK:
                loc.check()
            elif a.type == ActionType.UNCHECK:
                loc.uncheck()
            elif a.type == ActionType.PRESS:
                loc.press(a.arg)
            elif a.type == ActionType.HOVER:
                loc.hover()
            elif a.type == ActionType.DBLCLICK:
                loc.dblclick()
            elif a.type == ActionType.UPLOAD_FILE:
                loc.set_input_files(a.arg)
            elif a.type == ActionType.DRAG_TO:
                loc.drag_to(target)
            elif a.type == ActionType.EXPECT_VALUE and loc.input_value() != a.arg:
                idx, note = i, f"value actual: {loc.input_value()!r}"
                break
            elif a.type == ActionType.EXPECT_CHECKED and not loc.is_checked():
                idx, note = i, "checkbox/radio is not checked"
                break
            elif a.type == ActionType.EXPECT_ENABLED and not loc.is_enabled():
                idx, note = i, "element is disabled"
                break
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


def heal_all(browser, plan: PlaywrightPlan, max_rounds: int = 6,
             storage_state: str | None = None):
    """Chữa theo lô: dò bước hỏng → chữa → dò lại trên plan đã chữa, tới khi hết lỗi chữa được.

    Trả (các action đã chữa theo chỉ số, ghi chú + snapshot tại bước hỏng cuối cùng). Một mutation đổi nhiều locator
    cùng lúc (vd đổi id cả 3 ô đăng nhập) được chữa trong MỘT đề xuất thay vì tốn nhiều lượt ngân sách.
    """
    healed: dict[int, PlaywrightAction] = {}
    current = plan
    note, snap = "", ""
    for _ in range(max_rounds):
        page, idx, note, snap = probe(browser, current, storage_state=storage_state)
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
            state = payload.get("storage_state")
            if name == "snapshot":
                page = browser.new_page(storage_state=state) if state else browser.new_page()
                page.goto(payload["url"], wait_until="domcontentloaded", timeout=30000)
                with contextlib.suppress(Exception):
                    page.wait_for_load_state("networkidle", timeout=8000)
                return {"snapshot": snapshot(page, payload.get("chars", 6000))}
            plan = PlaywrightPlan.model_validate(payload["plan"])
            if name == "ground":
                page = browser.new_page(storage_state=state) if state else browser.new_page()
                records = ground_flow(page, plan.actions, snapshot_chars=payload.get("chars", SNAPSHOT_CHARS))
                return {"records": [r.model_dump() for r in records]}
            if name == "probe_heal":
                healed, evidence = heal_all(browser, plan, storage_state=state)
                return {"evidence": evidence, "healed": {str(k): v.model_dump(mode="json") for k, v in healed.items()}}
            raise ValueError(f"task không hỗ trợ: {name}")
        finally:
            browser.close()


def run_task(name: str, payload: dict, timeout: int = 180) -> dict:
    """Chạy tác vụ ở tiến trình con; lỗi browser phải dừng luồng thay vì trả kết quả rỗng."""
    child_env = os.environ.copy()
    child_env["PYTHONUTF8"] = "1"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "src.services.browser_tasks", name],
            input=json.dumps(payload), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
            cwd=Path(__file__).resolve().parents[2], env=child_env,
        )
    except subprocess.TimeoutExpired as exc:
        raise BrowserTaskError(f"Tác vụ {name} quá thời gian {timeout} giây") from exc
    except OSError as exc:
        raise BrowserTaskError(f"Không khởi chạy được tác vụ trình duyệt {name}") from exc
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        detail = next(
            (line for line in reversed(lines)
             if line.startswith(("playwright._impl._errors.", "ValueError:", "RuntimeError:", "OSError:"))),
            lines[-1] if lines else f"exit {proc.returncode}",
        )
        raise BrowserTaskError(detail)
    try:
        return json.loads(proc.stdout or "")
    except json.JSONDecodeError as exc:
        raise BrowserTaskError(f"Tác vụ {name} không trả JSON hợp lệ") from exc


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    print(json.dumps(_task(sys.argv[1], json.loads(sys.stdin.read())), ensure_ascii=False))
