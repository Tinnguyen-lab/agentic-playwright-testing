"""RQ2 — đo first-run pass rate của script Playwright do LLM SINH từ test case, chạy thật.

    python run_rq2.py --profile cloud   # DeepSeek (cần .env.cloud)
    python run_rq2.py                    # LLM trong .env (local)
    python run_rq2.py --mock             # offline smoke (plan dựng sẵn, số không có ý nghĩa)

Bộ test case cho SauceDemo (đăng nhập). Với mỗi test case: PlaywrightGenerationAgent.plan (LLM)
-> render script -> ExecutionAgent chạy thật -> ghi pass/fail. In first-run pass rate + JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.agents.execution_agent import ExecutionAgent
from src.agents.playwright_generation_agent import PlaywrightGenerationAgent
from src.models.playwright_artifacts import (
    ActionType, GeneratedScript, LocatorStrategy, PlaywrightAction, PlaywrightPlan,
)
from src.models.test_case import TestCase, TestStep, TestType
from src.services.script_template import render_script
from src.utils.cli import resolve_client

URL = "https://www.saucedemo.com/"
WORKDIR = Path("artifacts/exec_rq2")


def _test_cases() -> list[TestCase]:
    return [
        TestCase(id="SD-TC-01", title="Đăng nhập hợp lệ", type=TestType.POSITIVE,
                 steps=[TestStep(action="Nhập username 'standard_user' và password 'secret_sauce'"),
                        TestStep(action="Bấm nút Login", expected="Chuyển tới trang sản phẩm")],
                 expected_result="Đăng nhập thành công, URL là https://www.saucedemo.com/inventory.html"),
        TestCase(id="SD-TC-02", title="Sai mật khẩu", type=TestType.NEGATIVE,
                 steps=[TestStep(action="Nhập username 'standard_user' và password 'wrong_password'"),
                        TestStep(action="Bấm Login", expected="Hiện thông báo lỗi")],
                 expected_result="Hiện thông báo lỗi chứa 'Username and password do not match'"),
        TestCase(id="SD-TC-03", title="Tài khoản bị khoá", type=TestType.NEGATIVE,
                 steps=[TestStep(action="Nhập username 'locked_out_user' và password 'secret_sauce'"),
                        TestStep(action="Bấm Login", expected="Hiện thông báo bị khoá")],
                 expected_result="Hiện thông báo chứa 'Sorry, this user has been locked out'"),
    ]


def _mock_plan() -> PlaywrightPlan:
    return PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.GOTO, arg=URL),
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

    ap = argparse.ArgumentParser(description="RQ2: first-run pass rate của script do LLM sinh")
    ap.add_argument("--profile", help="Hồ sơ .env: 'cloud' -> .env.cloud")
    ap.add_argument("--mock", action="store_true", help="Offline smoke (plan dựng sẵn)")
    ap.add_argument("--out", default="rq2_results.json")
    args = ap.parse_args(argv)

    client, model = resolve_client(args.profile, args.mock, _mock_plan())
    agent = PlaywrightGenerationAgent(client, model_name=model)
    executor = ExecutionAgent()
    WORKDIR.mkdir(parents=True, exist_ok=True)

    rows = []
    passed = 0
    for tc in _test_cases():
        plan = agent.plan(tc, URL)
        script = GeneratedScript(test_case_id=tc.id, code=render_script(plan, screenshot=f"{tc.id}.png"))
        result = executor.run(script, WORKDIR)
        ok = result.status.value == "passed"
        passed += ok
        rows.append({"id": tc.id, "title": tc.title, "status": result.status.value,
                     "n_actions": len(plan.actions)})
        print(f"[{tc.id}] {tc.title}: {result.status.value.upper()}")

    n = len(rows)
    rate = passed / n if n else 0.0
    print(f"\n=== RQ2 first-run pass rate: {passed}/{n} = {rate:.0%} | model={model} ===")
    Path(args.out).write_text(json.dumps(
        {"model": model, "target": URL, "n": n, "passed": passed, "first_run_pass_rate": rate, "cases": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
