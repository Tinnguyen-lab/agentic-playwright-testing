"""RQ2 — đo first-run pass rate của script Playwright do LLM SINH từ test case, chạy thật.

    python run_rq2.py --profile cloud   # DeepSeek (cần .env.cloud)
    python run_rq2.py                    # LLM trong .env (local)

Đọc catalog target từ datasets/reference/rq2_targets.json (data-driven — cộng dồn tới >=50).
Mỗi target: PlaywrightGenerationAgent.plan (LLM) -> render script -> ExecutionAgent chạy thật
-> ghi pass/fail. In first-run pass rate theo site + tổng + JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from src.agents.execution_agent import ExecutionAgent
from src.agents.playwright_generation_agent import PlaywrightGenerationAgent
from src.models.playwright_artifacts import (
    ActionType, GeneratedScript, LocatorStrategy, PlaywrightAction, PlaywrightPlan,
)
from src.models.test_case import TestCase, TestStep, TestType
from src.services.script_template import render_script
from src.utils.cli import resolve_client

CATALOG = "datasets/reference/rq2_targets.json"
WORKDIR = Path("artifacts/exec_rq2")


def _load_targets(path: str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for t in data["targets"]:
        tc = TestCase(id=t["id"], title=t.get("title", t["id"]), type=TestType(t.get("type", "positive")),
                      steps=[TestStep(action=s) for s in t["steps"]], expected_result=t["expected_result"])
        out.append((t.get("site", "?"), t["url"], tc))
    return out


def _mock_plan() -> PlaywrightPlan:
    return PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.GOTO, arg="https://www.saucedemo.com/"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="standard_user"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Password", arg="secret_sauce"),
        PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button", role_name="Login"),
        PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://www.saucedemo.com/inventory.html"),
    ])


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
    args = ap.parse_args(argv)

    client, model = resolve_client(args.profile, args.mock, _mock_plan())
    agent = PlaywrightGenerationAgent(client, model_name=model)
    executor = ExecutionAgent()
    WORKDIR.mkdir(parents=True, exist_ok=True)

    targets = _load_targets(args.catalog)
    print(f"[i] {len(targets)} target | model={model}")
    by_site = defaultdict(lambda: [0, 0])
    rows = []
    total_pass = 0
    for site, url, tc in targets:
        plan = agent.plan(tc, url)
        script = GeneratedScript(test_case_id=tc.id, code=render_script(plan, screenshot=f"{tc.id}.png"))
        result = executor.run(script, WORKDIR)
        ok = result.status.value == "passed"
        total_pass += ok
        by_site[site][0] += ok
        by_site[site][1] += 1
        rows.append({"id": tc.id, "site": site, "url": url, "status": result.status.value})
        print(f"  [{tc.id:6}] {site:24} {result.status.value.upper()}")

    n = len(targets)
    print("\n--- Theo site ---")
    for site, (p, tot) in sorted(by_site.items()):
        print(f"  {site:24} {p}/{tot} = {p/tot:.0%}")
    print(f"\n=== RQ2 first-run pass rate: {total_pass}/{n} = {total_pass/n:.0%} | {len(by_site)} site | model={model} ===")

    Path(args.out).write_text(json.dumps(
        {"model": model, "n": n, "passed": total_pass, "first_run_pass_rate": total_pass / n if n else 0.0,
         "by_site": {s: {"passed": v[0], "n": v[1]} for s, v in by_site.items()}, "cases": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
