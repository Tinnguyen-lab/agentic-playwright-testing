"""RQ4-S: mô phỏng kiểm soát cho vai trò của cổng review.

Đây *không phải* thí nghiệm RQ4 có người tham gia. Hai nhánh dùng sáu test
fixture cố định trên ShopLab: ``system_only`` thiếu có chủ đích hai assertion
oracle, còn ``reviewed`` bổ sung đúng hai assertion đó. Cả hai được chấm bằng
mutation thật của ShopLab. Mục tiêu là kiểm tra cơ chế chấm và minh hoạ vì sao
approval gate cần thiết; không suy diễn năng suất hay SUS của con người.

    python tools/rq4/simulate.py
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from run_rq3 import serve  # noqa: E402
from tools.rq4.rq4 import MUTANT, _run  # noqa: E402


BASE = "http://127.0.0.1:5100"


def _login(user: str = "alice", password: str = "secret123") -> str:
    return f'''page.goto("{BASE}/login")
    page.get_by_label("Username").fill("{user}")
    page.get_by_label("Password").fill("{password}")
    page.get_by_role("button", name="Login").click()'''


def cases() -> dict[str, dict[str, dict[str, str]]]:
    """Trả fixture script cho hai nhánh, phân tách hoàn toàn với LLM output."""
    a1 = f'''from playwright.sync_api import expect

def test_uc1_login_redirect(page):
    {_login()}
    expect(page).to_have_url("{BASE}/products")
    expect(page.get_by_role("heading", name="Products")).to_be_visible()
'''
    # Mô phỏng LLM thực hiện action nhưng bỏ expected error cụ thể.
    a2_auto = f'''def test_uc2_wrong_password(page):
    {_login(password="wrong")}
    assert page.url.endswith("/login")
'''
    a2_reviewed = f'''from playwright.sync_api import expect

def test_uc2_wrong_password(page):
    {_login(password="wrong")}
    expect(page.get_by_role("alert")).to_have_text("Invalid username or password")
'''
    a3 = f'''from playwright.sync_api import expect

def test_uc3_add_to_cart(page):
    {_login()}
    page.get_by_test_id("add-backpack").click()
    expect(page.get_by_test_id("cart-count")).to_have_text("1")
'''
    b1 = f'''from playwright.sync_api import expect

def test_uc1_cart_total(page):
    {_login()}
    page.get_by_test_id("add-backpack").click()
    page.get_by_test_id("add-bike-light").click()
    page.goto("{BASE}/cart")
    expect(page.locator("#total")).to_have_text("Total: $39.98")
'''
    # Mô phỏng một test 'chạy xanh' nhưng không có assertion về validation.
    b2_auto = f'''def test_uc2_first_name_required(page):
    {_login()}
    page.goto("{BASE}/checkout")
    page.get_by_label("Last name").fill("Nguyen")
    page.get_by_label("Zip code").fill("70000")
    page.get_by_role("button", name="Continue").click()
'''
    b2_reviewed = f'''from playwright.sync_api import expect

def test_uc2_first_name_required(page):
    {_login()}
    page.goto("{BASE}/checkout")
    page.get_by_label("Last name").fill("Nguyen")
    page.get_by_label("Zip code").fill("70000")
    page.get_by_role("button", name="Continue").click()
    expect(page.get_by_role("alert")).to_have_text("First name is required")
'''
    b3 = f'''from playwright.sync_api import expect

def test_uc3_locked_account(page):
    {_login(user="bob")}
    expect(page.get_by_role("alert")).to_have_text("Account is locked")
'''
    automatic = {"A": {"uc1": a1, "uc2": a2_auto, "uc3": a3},
                 "B": {"uc1": b1, "uc2": b2_auto, "uc3": b3}}
    reviewed = {"A": {"uc1": a1, "uc2": a2_reviewed, "uc3": a3},
                "B": {"uc1": b1, "uc2": b2_reviewed, "uc3": b3}}
    return {"system_only": automatic, "reviewed": reviewed}


def write_cases(out: Path) -> None:
    for arm, tasks in cases().items():
        for task, scripts in tasks.items():
            folder = out / arm / task
            folder.mkdir(parents=True, exist_ok=True)
            for uc, code in scripts.items():
                (folder / f"{uc}_shoplab.py").write_text(code, encoding="utf-8")


def evaluate_task(folder: Path, task: str) -> dict:
    tests = sorted(folder.glob("uc*.py"))
    by_uc: dict[str, list[Path]] = defaultdict(list)
    for test in tests:
        by_uc[test.name[:3]].append(test)
    with serve("v0", 5100):
        on_v0 = {test: _run(test) for test in tests}
    on_mut: dict[Path, bool] = {}
    for uc, variant in MUTANT[task].items():
        with serve(variant, 5100):
            on_mut.update({test: _run(test) for test in by_uc[uc]})
    ucs = {uc: {"pass_v0": any(on_v0[t] for t in by_uc[uc]),
                "fails_required_mutation": any(on_v0[t] and not on_mut[t] for t in by_uc[uc])}
           for uc in MUTANT[task]}
    return {"task": task, "ucs": ucs,
            "valid_ucs": sum(row["fails_required_mutation"] for row in ucs.values()),
            "runnable_ucs": sum(row["pass_v0"] for row in ucs.values())}


def run(out: Path) -> dict:
    if out.exists():
        shutil.rmtree(out)
    write_cases(out)
    arms = {}
    for arm in cases():
        task_results = [evaluate_task(out / arm / task, task) for task in ("A", "B")]
        valid = sum(item["valid_ucs"] for item in task_results)
        runnable = sum(item["runnable_ucs"] for item in task_results)
        arms[arm] = {"tasks": task_results, "candidate_tests": 6, "runnable_tests": runnable,
                     "semantically_valid_tests": valid,
                     "semantic_precision_pct": round(100 * valid / 6, 1),
                     "semantic_coverage_pct": round(100 * valid / 6, 1)}
    result = {
        "kind": "controlled_simulation_not_human_study",
        "comparison": "system_only versus system_plus_oracle_review",
        "fixture_rule": "Two expected-result assertions are intentionally omitted in system_only and restored in reviewed.",
        "review_actions": [
            {"task": "A", "uc": "UC-2", "action": "add exact invalid-password error assertion"},
            {"task": "B", "uc": "UC-2", "action": "add required-first-name error assertion"},
        ],
        "arms": arms,
        "interpretation_limit": "No completion time, manual effort, SUS, or human accuracy is measured or inferred.",
    }
    (out / "rq4_simulation_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RQ4-S controlled review-gate simulation")
    parser.add_argument("--out", default="artifacts/rq4_simulation")
    args = parser.parse_args(argv)
    result = run(ROOT / args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
