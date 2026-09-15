"""CLI Playwright Generation + Execution trên website đích (mặc định SauceDemo).

    # demo offline-plan (mock plan đăng nhập) chạy LIVE trên SauceDemo:
    python run_playwright_pipeline.py --mock
    # từ test case thật (test_design.json) + LLM:
    python run_playwright_pipeline.py --from test_design.json --profile cloud
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.agents.execution_agent import ExecutionAgent
from src.agents.playwright_generation_agent import PlaywrightGenerationAgent, live_count_fn
from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction, PlaywrightPlan
from src.models.test_case import TestCase, TestStep, TestType
from src.utils.cli import resolve_client

DEFAULT_URL = "https://www.saucedemo.com/"
WORKDIR = Path("artifacts/exec")


def default_demo_test_case() -> TestCase:
    return TestCase(
        id="REQ-001-TC-01", requirement_id="REQ-001", title="Đăng nhập hợp lệ", type=TestType.POSITIVE,
        steps=[TestStep(action="Nhập standard_user / secret_sauce và bấm Login", expected="Vào trang inventory")],
        expected_result="Chuyển tới trang inventory",
    )


def default_mock_plan() -> PlaywrightPlan:
    return PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.GOTO, arg=DEFAULT_URL),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="standard_user"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Password", arg="secret_sauce"),
        PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button", role_name="Login"),
        PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://www.saucedemo.com/inventory.html"),
    ])


def load_test_cases(src: str) -> list[TestCase]:
    data = json.loads(Path(src).read_text(encoding="utf-8"))
    return [TestCase.model_validate(tc) for tc in data["test_cases"]]


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Playwright Generation + Execution")
    ap.add_argument("--from", dest="src", help="test_design.json (test case đã approved)")
    ap.add_argument("--url", default=DEFAULT_URL, help="Website đích")
    ap.add_argument("--mock", action="store_true", help="Dùng plan giả lập (offline plan) — demo login")
    ap.add_argument("--profile", help="Hồ sơ .env cho LLM sinh plan")
    ap.add_argument("--out", default="playwright_results.json")
    args = ap.parse_args(argv)

    test_cases = load_test_cases(args.src) if args.src else [default_demo_test_case()]
    client, model_name = resolve_client(args.profile, args.mock, default_mock_plan())
    agent = PlaywrightGenerationAgent(client, model_name=model_name)
    executor = ExecutionAgent()
    WORKDIR.mkdir(parents=True, exist_ok=True)

    out_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        counter = live_count_fn(page)
        for tc in test_cases:
            page.goto(args.url)
            script = agent.generate(tc, args.url, count_fn=counter, screenshot=f"{tc.id}.png")
            result = executor.run(script, WORKDIR)

            grounded_ok = sum(1 for g in script.grounding if g.ok)
            print(f"\n[{tc.id}] {tc.title}")
            print(f"  grounding: {grounded_ok}/{len(script.grounding)} locator khớp-đúng-1")
            for g in script.grounding:
                flag = "✓" if g.ok else "⚠"
                print(f"    {flag} [{g.strategy}] {g.value} -> {g.matched_count}")
            print(f"  execution: {result.status.value} (exit={result.exit_code})")
            if result.artifacts:
                print(f"  evidence: {', '.join(result.artifacts)}")

            out_results.append({
                "test_case_id": tc.id,
                "grounding": [g.model_dump(mode="json") for g in script.grounding],
                "execution": result.model_dump(mode="json"),
            })
        browser.close()

    Path(args.out).write_text(json.dumps(out_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[✓] Đã ghi: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
