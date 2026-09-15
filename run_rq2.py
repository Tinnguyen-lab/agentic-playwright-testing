"""RQ2 — đo first-run pass rate của script Playwright do LLM SINH từ test case, chạy thật.

    python run_rq2.py --profile cloud   # DeepSeek (cần .env.cloud)
    python run_rq2.py                    # LLM trong .env (local)
    python run_rq2.py --mock             # offline smoke (plan dựng sẵn, số không có ý nghĩa)

Nhiều target thật (SauceDemo, the-internet, practice-test-login). Với mỗi test case:
PlaywrightGenerationAgent.plan (LLM) -> render script -> ExecutionAgent chạy thật -> ghi pass/fail.
In first-run pass rate theo từng target + tổng + JSON.
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

WORKDIR = Path("artifacts/exec_rq2")


def _tc(id_, title, ttype, steps, expected):
    return TestCase(id=id_, title=title, type=ttype,
                    steps=[TestStep(action=a, expected=e) for a, e in steps], expected_result=expected)


def _targets() -> list[tuple[str, str, list[TestCase]]]:
    return [
        ("SauceDemo", "https://www.saucedemo.com/", [
            _tc("SD-01", "Đăng nhập hợp lệ", TestType.POSITIVE,
                [("Nhập username 'standard_user' và password 'secret_sauce'", ""),
                 ("Bấm nút Login", "Chuyển tới trang sản phẩm")],
                "Đăng nhập thành công, URL là https://www.saucedemo.com/inventory.html"),
            _tc("SD-02", "Sai mật khẩu", TestType.NEGATIVE,
                [("Nhập username 'standard_user' và password 'wrong_password'", ""),
                 ("Bấm Login", "Hiện thông báo lỗi")],
                "Hiện thông báo lỗi chứa 'Username and password do not match'"),
            _tc("SD-03", "Tài khoản bị khoá", TestType.NEGATIVE,
                [("Nhập username 'locked_out_user' và password 'secret_sauce'", ""),
                 ("Bấm Login", "Hiện thông báo bị khoá")],
                "Hiện thông báo chứa 'Sorry, this user has been locked out'"),
        ]),
        ("the-internet", "https://the-internet.herokuapp.com/login", [
            _tc("TI-01", "Đăng nhập hợp lệ", TestType.POSITIVE,
                [("Nhập username 'tomsmith' và password 'SuperSecretPassword!'", ""),
                 ("Bấm nút Login", "Vào khu vực bảo mật")],
                "Hiện thông báo chứa 'You logged into a secure area!'"),
            _tc("TI-02", "Sai thông tin", TestType.NEGATIVE,
                [("Nhập username 'baduser' và password 'badpass'", ""),
                 ("Bấm Login", "Hiện lỗi")],
                "Hiện thông báo chứa 'Your username is invalid!'"),
        ]),
        ("practice-test-login", "https://practicetestautomation.com/practice-test-login/", [
            _tc("PT-01", "Đăng nhập hợp lệ", TestType.POSITIVE,
                [("Nhập username 'student' và password 'Password123'", ""),
                 ("Bấm nút Submit", "Đăng nhập thành công")],
                "Hiện thông báo chứa 'Logged In Successfully'"),
            _tc("PT-02", "Sai username", TestType.NEGATIVE,
                [("Nhập username 'incorrectUser' và password 'Password123'", ""),
                 ("Bấm Submit", "Hiện lỗi")],
                "Hiện thông báo chứa 'Your username is invalid!'"),
        ]),
    ]


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
    ap.add_argument("--out", default="rq2_results.json")
    args = ap.parse_args(argv)

    client, model = resolve_client(args.profile, args.mock, _mock_plan())
    agent = PlaywrightGenerationAgent(client, model_name=model)
    executor = ExecutionAgent()
    WORKDIR.mkdir(parents=True, exist_ok=True)

    targets_out = []
    total_pass = total_n = 0
    for name, url, tcs in _targets():
        print(f"\n### Target: {name} ({url})")
        tp = 0
        cases = []
        for tc in tcs:
            plan = agent.plan(tc, url)
            script = GeneratedScript(test_case_id=tc.id, code=render_script(plan, screenshot=f"{tc.id}.png"))
            result = executor.run(script, WORKDIR)
            ok = result.status.value == "passed"
            tp += ok
            cases.append({"id": tc.id, "title": tc.title, "status": result.status.value})
            print(f"  [{tc.id}] {tc.title}: {result.status.value.upper()}")
        total_pass += tp
        total_n += len(tcs)
        targets_out.append({"target": name, "url": url, "passed": tp, "n": len(tcs),
                            "first_run_pass_rate": tp / len(tcs), "cases": cases})
        print(f"  -> {name}: {tp}/{len(tcs)} = {tp/len(tcs):.0%}")

    print(f"\n=== RQ2 first-run pass rate (tổng, {len(targets_out)} target): "
          f"{total_pass}/{total_n} = {total_pass/total_n:.0%} | model={model} ===")
    Path(args.out).write_text(json.dumps(
        {"model": model, "n_targets": len(targets_out), "passed": total_pass, "n": total_n,
         "first_run_pass_rate": total_pass / total_n if total_n else 0.0, "targets": targets_out},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
