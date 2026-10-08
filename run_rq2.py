"""RQ2 — đo first-run pass rate của script Playwright do LLM SINH từ test case, chạy thật.

    python run_rq2.py --profile cloud   # DeepSeek (cần .env.cloud)
    python run_rq2.py                    # LLM trong .env (local)
    python run_rq2.py --context both     # baseline vs DOM-aware (aria snapshot) trên CÙNG target

Đọc catalog target từ datasets/reference/rq2_targets.json (data-driven — cộng dồn tới >=50).
Mỗi target: PlaywrightGenerationAgent.plan (LLM) -> render script -> ExecutionAgent chạy thật
-> ghi pass/fail + lỗi. In first-run pass rate theo site + tổng + JSON.
Nhánh `aria`: chụp aria snapshot trang đích đưa vào prompt (RQ2: DOM có giúp không?).
"""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
from collections import defaultdict
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.agents.execution_agent import ExecutionAgent
from src.agents.playwright_generation_agent import PlaywrightGenerationAgent, ground_flow, grounding_feedback
from src.models.playwright_artifacts import (
    ActionType, GeneratedScript, LocatorStrategy, PlaywrightAction, PlaywrightPlan,
)
from src.models.test_case import TestCase, TestStep, TestType
from src.services.script_template import render_script
from src.utils.cli import resolve_client

CATALOG = "datasets/reference/rq2_targets.json"
WORKDIR = Path("artifacts/exec_rq2")
INFRA_HANG = "Page.goto: Timeout"
SNAPSHOT_CHARS = 6000  # ponytail: cắt cứng, đủ cho trang demo; trang lớn cần lọc theo vùng


def _error_line(stderr: str) -> str:
    """Dòng lỗi có nghĩa cuối cùng (vd 'TimeoutError: ...') để phân loại nguyên nhân fail."""
    lines = [l.strip() for l in stderr.splitlines() if "Error" in l or "error" in l]
    return (lines[-1] if lines else stderr.strip()[-200:])[:300]


def _aria_snapshots(urls) -> dict[str, str]:
    """Mở mỗi URL một lần, lấy aria snapshot của <body> (lỗi -> chuỗi rỗng = như baseline)."""
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-http2"])  # giống script_template
        page = browser.new_page()
        for url in dict.fromkeys(urls):
            try:
                page.goto(url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            try:
                out[url] = page.locator("body").aria_snapshot()[:SNAPSHOT_CHARS]
            except Exception as e:
                print(f"  [!] snapshot lỗi {url}: {e}")
                out[url] = ""
        browser.close()
    return out


def _load_targets(path: str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for t in data["targets"]:
        tc = TestCase(id=t["id"], title=t.get("title", t["id"]), type=TestType(t.get("type", "positive")),
                      steps=[TestStep(action=s) for s in t["steps"]], expected_result=t["expected_result"])
        out.append((t.get("site", "?"), t["url"], tc, t.get("oracle", [])))
    return out


def _mock_plan() -> PlaywrightPlan:
    return PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.GOTO, arg="https://www.saucedemo.com/"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="standard_user"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Password", arg="secret_sauce"),
        PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button", role_name="Login"),
        PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://www.saucedemo.com/inventory.html"),
    ])


def _ground_and_refine(agent, browser, tc, url, ctx, plan):
    """Grounding plan trên trang thật; có locator khớp != 1 thì phản hồi cho LLM sinh lại đúng 1 lần."""
    page_ctx = browser.new_context()
    try:
        records = ground_flow(page_ctx.new_page(), plan.actions, snapshot_chars=SNAPSHOT_CHARS)
    except Exception:  # trang không tải được -> giữ plan, không phản hồi
        records = []
    finally:
        page_ctx.close()
    feedback = grounding_feedback(plan, records)
    if feedback is None:
        return plan, False
    return agent.plan(tc, url, page_context=ctx, feedback=feedback), True


def _paired(rx, ry, x, y):
    a = {r["id"]: r["status"] == "passed" for r in rx["cases"]}
    b = {r["id"]: r["status"] == "passed" for r in ry["cases"]}
    return {"both_pass": sum(a[i] and b[i] for i in a), "both_fail": sum(not a[i] and not b[i] for i in a),
            f"{y}_only": sum(b[i] and not a[i] for i in a), f"{x}_only": sum(a[i] and not b[i] for i in a)}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="RQ2: first-run pass rate của script do LLM sinh (nhiều target)")
    ap.add_argument("--profile", help="Hồ sơ .env: 'cloud' -> .env.cloud")
    ap.add_argument("--mock", action="store_true", help="Offline smoke (plan dựng sẵn)")
    ap.add_argument("--catalog", default=CATALOG)
    ap.add_argument("--out", default="rq2_results.json")
    ap.add_argument("--context", choices=["none", "aria", "aria_loop", "both", "all", "oracle"], default="none",
                    help="none = baseline (chỉ test case); aria = kèm aria snapshot trang đích; aria_loop = aria + "
                         "grounding trên trang thật, locator khớp != 1 thì phản hồi để LLM sinh lại 1 lần; "
                         "both = none+aria; all = none+aria+aria_loop; oracle = plan viết tay (không gọi LLM)")
    args = ap.parse_args(argv)

    client, model = resolve_client(args.profile, args.mock, _mock_plan())
    agent = PlaywrightGenerationAgent(client, model_name=model)
    executor = ExecutionAgent()
    WORKDIR.mkdir(parents=True, exist_ok=True)

    targets = _load_targets(args.catalog)
    conditions = {"both": ["none", "aria"], "all": ["none", "aria", "aria_loop"]}.get(args.context, [args.context])
    snaps = _aria_snapshots([t[1] for t in targets]) if {"aria", "aria_loop"} & set(conditions) else {}
    print(f"[i] {len(targets)} target | model={model} | context={conditions}")

    stack = contextlib.ExitStack()
    browser = (stack.enter_context(sync_playwright()).chromium.launch(args=["--disable-http2"])
               if "aria_loop" in conditions else None)
    results = {}
    for cond in conditions:
        print(f"\n### context={cond}")
        by_site = defaultdict(lambda: [0, 0])
        rows = []
        for site, url, tc, oracle in targets:
            ctx = snaps.get(url) if cond in ("aria", "aria_loop") else None
            infra_retry = refined = False
            try:
                plan = (PlaywrightPlan(actions=oracle) if cond == "oracle"  # cận trên: target khả thi?
                        else agent.plan(tc, url, page_context=ctx))
                if cond == "aria_loop":
                    plan, refined = _ground_and_refine(agent, browser, tc, url, ctx, plan)
                script = GeneratedScript(test_case_id=tc.id, code=render_script(plan, screenshot=f"{tc.id}.png"))
                result = executor.run(script, WORKDIR / cond)
                if result.status.value != "passed" and INFRA_HANG in result.stderr:
                    # site demo treo khi tải trang = lỗi hạ tầng, không phải lỗi script -> chạy lại CÙNG script 1 lần
                    infra_retry = True
                    result = executor.run(script, WORKDIR / cond)
                status, err = result.status.value, ("" if result.status.value == "passed" else _error_line(result.stderr))
            except Exception as e:  # LLM trả plan hỏng cũng tính là fail lần đầu
                status, err = "error", f"plan: {e}"[:300]
            ok = status == "passed"
            by_site[site][0] += ok
            by_site[site][1] += 1
            rows.append({"id": tc.id, "site": site, "url": url, "type": tc.type.value, "status": status, "error": err,
                         "infra_retry": infra_retry, "refined": refined})
            print(f"  [{tc.id:6}] {site:24} {status.upper():7} {err[:90]}")
        n, passed = len(rows), sum(r["status"] == "passed" for r in rows)
        results[cond] = {"n": n, "passed": passed, "first_run_pass_rate": passed / n if n else 0.0,
                         "by_site": {s: {"passed": v[0], "n": v[1]} for s, v in sorted(by_site.items())},
                         "cases": rows}

    print("\n--- Theo site ---")
    for site in sorted({t[0] for t in targets}):
        cells = "  ".join(f"{c}: {results[c]['by_site'][site]['passed']}/{results[c]['by_site'][site]['n']}" for c in conditions)
        print(f"  {site:24} {cells}")
    for c in conditions:
        r = results[c]
        print(f"=== RQ2 [{c}] first-run pass rate: {r['passed']}/{r['n']} = {r['first_run_pass_rate']:.0%} | model={model} ===")

    stack.close()
    out = {"model": model, "conditions": results}
    # cặp trên cùng target -> dữ liệu cho McNemar; "paired" giữ dạng cũ (none vs aria) cho báo cáo
    pairs = {f"{x}__{y}": _paired(results[x], results[y], x, y)
             for i, x in enumerate(conditions) for y in conditions[i + 1:]}
    if pairs:
        out["paired_all"] = pairs
        out["paired"] = pairs.get("none__aria") or next(iter(pairs.values()))
        print(f"[i] Paired: {pairs}")
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
