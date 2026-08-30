"""Capstone: pipeline END-TO-END trên SauceDemo, đóng vòng human-governed + traceable.

Requirement(approve) -> Test Case(approve) -> Playwright gen+grounding+execution
  -> nếu FAIL: Repair proposal (gated bởi policy + approval, KHÔNG tự áp dụng)
  -> Traceability report.

    python run_full_pipeline.py            # demo tất định (mock LLM) chạy LIVE SauceDemo

Demo: 1 case đăng nhập hợp lệ (PASS) + 1 case cố ý sai locator (FAIL -> repair LOW chờ duyệt).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.agents.execution_agent import ExecutionAgent
from src.agents.playwright_generation_agent import ground_actions, live_count_fn
from src.agents.repair_agent import RepairAgent
from src.models.approval import ApprovalDecision, ApprovalStatus
from src.models.playwright_artifacts import (
    ActionType, GeneratedScript, LocatorStrategy, PlaywrightAction, PlaywrightPlan,
)
from src.models.repair import FailureType, RepairDraft, RepairOutcome
from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCase, TestStep, TestType
from src.services.llm_client import MockLLMClient
from src.services.script_template import render_script
from src.services.traceability import build_report, render_markdown

URL = "https://www.saucedemo.com/"
WORKDIR = Path("artifacts/exec")
REPORT_MD = Path("docs/development/traceability-report.md")


def _login_actions(username_placeholder: str) -> list[PlaywrightAction]:
    return [
        PlaywrightAction(type=ActionType.GOTO, arg=URL),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value=username_placeholder, arg="standard_user"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Password", arg="secret_sauce"),
        PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button", role_name="Login"),
        PlaywrightAction(type=ActionType.EXPECT_URL, arg="https://www.saucedemo.com/inventory.html"),
    ]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # 1. Requirement (approved) — AG-01
    requirement = StructuredRequirement(
        id="REQ-001", title="Đăng nhập", actor="Người dùng",
        action="Đăng nhập bằng tài khoản hợp lệ", expected_outcome="Vào trang sản phẩm",
    )
    ApprovalDecision(artifact_id=requirement.id, status=ApprovalStatus.APPROVED, decided_by="demo")

    # 2. Test cases (approved) — AG-02
    tc_ok = TestCase(id="REQ-001-TC-01", requirement_id="REQ-001", title="Đăng nhập hợp lệ",
                     type=TestType.POSITIVE, steps=[TestStep(action="Đăng nhập standard_user", expected="Vào inventory")])
    tc_bad = TestCase(id="REQ-001-TC-02", requirement_id="REQ-001", title="Đăng nhập (locator lỗi)",
                      type=TestType.POSITIVE, steps=[TestStep(action="Đăng nhập standard_user", expected="Vào inventory")])
    plans = {
        tc_ok.id: PlaywrightPlan(test_case_id=tc_ok.id, target_url=URL, actions=_login_actions("Username")),
        tc_bad.id: PlaywrightPlan(test_case_id=tc_bad.id, target_url=URL, actions=_login_actions("Usernamex")),  # sai chủ đích
    }

    executor = ExecutionAgent()
    WORKDIR.mkdir(parents=True, exist_ok=True)
    executions = []
    repairs = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        counter = live_count_fn(page)

        for tc in (tc_ok, tc_bad):
            plan = plans[tc.id]
            page.goto(URL)
            grounding = ground_actions(plan.actions, counter)
            script = GeneratedScript(test_case_id=tc.id, code=render_script(plan, screenshot=f"{tc.id}.png"), grounding=grounding)
            result = executor.run(script, WORKDIR)
            executions.append(result)

            grounded_ok = sum(1 for g in grounding if g.ok)
            print(f"\n[{tc.id}] {tc.title}")
            print(f"  grounding: {grounded_ok}/{len(grounding)} khớp-đúng-1 | execution: {result.status.value}")

            if result.status.value != "passed":
                # 3. Repair Agent — constrained, gated. Mock đề xuất sửa locator (Usernamex -> Username).
                fixed = PlaywrightPlan(test_case_id=tc.id, target_url=URL, actions=_login_actions("Username"))
                draft = RepairDraft(new_plan=fixed, failure_type=FailureType.LOCATOR_NOT_FOUND,
                                    reason="Placeholder sai: 'Usernamex' -> 'Username'")
                proposal = RepairAgent(MockLLMClient(draft), model_name="mock").propose(plan, result, tc, attempt=1)
                repairs.append(proposal)
                print(f"  repair: risk={proposal.risk_level.value} | outcome={proposal.outcome.value} "
                      f"| requires_approval={proposal.requires_approval} | changed={proposal.changed_kinds}")
                print("  -> ĐỀ XUẤT chờ người duyệt (AG-03..05), agent KHÔNG tự áp dụng.")
        browser.close()

    # 4. Traceability report
    report = build_report(["REQ-001"], [tc_ok, tc_bad], executions, repairs)
    print(f"\n=== TRACEABILITY ===")
    print(f"requirement_coverage={report['requirement_coverage']:.0%} "
          f"| executed_coverage={report['executed_coverage']:.0%} | pass_rate={report['pass_rate']:.0%}")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    Path("full_pipeline_results.json").write_text(
        json.dumps({"executions": [e.model_dump(mode="json") for e in executions],
                    "repairs": [r.model_dump(mode="json") for r in repairs],
                    "traceability": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] Traceability report: {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
