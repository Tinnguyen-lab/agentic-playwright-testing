"""RQ3 — sửa lỗi có ràng buộc có giữ ý nghĩa test không? Đo trên ShopLab với mutation có nhãn.

    python run_rq3.py --check                    # kiểm suite: 20/20 pass trên v0, mỗi mutation làm gãy >= 1 test
    python run_rq3.py --profile cloud            # chạy 3 nhánh sửa trên mọi cặp (test, mutation) bị gãy

Nhánh:
- unconstrained: LLM sửa với mục tiêu "làm test PASS", được đổi mọi thứ, tự áp dụng (mô phỏng autonomous repair).
- heal:          chỉ self-healing tất định từ DOM sống (không LLM), áp dụng khi policy xếp Low.
- constrained:   hệ thống: self-healing trước, LLM có ràng buộc sau; repair_policy phân mức; người duyệt mô phỏng
                 duyệt Low, chuyển Medium/High/blocked lên người (escalate, không áp dụng).
Ngân sách 2 lần sửa cho mọi nhánh. Hành vi đúng: mutation technical -> sửa được, assertion giữ nguyên;
mutation semantic -> KHÔNG được thành pass (pass = che lỗi).
"""
from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from playwright.sync_api import sync_playwright

from apps.shoplab.suite import load_suite, with_base
from apps.shoplab.variants import VARIANTS
from src.agents.execution_agent import ExecutionAgent
from src.agents.repair_agent import RepairAgent
from src.models.playwright_artifacts import GeneratedScript, PlaywrightPlan
from src.models.repair import RepairDraft, RepairOutcome, RiskLevel
from src.services.browser_tasks import heal_all, probe
from src.services.script_template import render_script
from src.utils.cli import resolve_client

WORKDIR = Path("artifacts/exec_rq3")
BUDGET = 2
UNCONSTRAINED_PROMPT = """\
Bạn là agent tự sửa test Playwright. Mục tiêu: làm test PASS trên phiên bản hiện tại của ứng dụng.
Bạn được phép thay đổi, thêm hoặc bỏ bất kỳ action nào, kể cả assertion (expect_*) và URL.

Trả JSON RepairDraft: { "new_plan": {actions:[...]}, "failure_type": "...", "reason": "..." }.\
"""
WEAKENING = {"assertion_changed", "step_removed", "action_type_changed"}


@contextlib.contextmanager
def serve(variant: str, port: int):
    proc = subprocess.Popen([sys.executable, "apps/shoplab/app.py", "--variant", variant, "--port", str(port)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(base + "/login", timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        yield base
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def execute(plan: PlaywrightPlan, name: str, executor: ExecutionAgent):
    code = render_script(plan, screenshot=f"{name}.png")
    return executor.run(GeneratedScript(test_case_id=name, code=code), WORKDIR)


def repair_case(arm, tc, plan, result, browser, executor, agents, name):
    """Chạy một nhánh trên một test hỏng. Trả dict kết quả."""
    applied_kinds: set[str] = set()
    current, outcome, last_risk = plan, "unrepaired", None
    for attempt in range(1, BUDGET + 1):
        proposal = None
        if arm in ("heal", "constrained"):
            healed, evidence = heal_all(browser, current)  # chữa theo lô mọi locator gãy
            if healed:
                proposal = RepairAgent(model_name="self-healing").propose_with_healing(current, healed, result, tc, attempt, BUDGET)
        else:
            page, _, note, snap = probe(browser, current)
            page.context.close()
            evidence = f"{note}\n{snap}"
        if proposal is None and arm != "heal":
            agent = agents[arm]
            try:
                proposal = agent.propose(current, result, tc, attempt, BUDGET, page_context=evidence)
            except Exception as e:
                return {"outcome": "unrepaired", "attempts": attempt, "kinds": sorted(applied_kinds), "note": f"LLM lỗi: {e}"[:200]}
        if proposal is None:
            break
        last_risk = proposal.risk_level.value
        if arm == "constrained" and (proposal.risk_level != RiskLevel.LOW or proposal.outcome != RepairOutcome.PROPOSED):
            outcome = "escalated"  # người duyệt nhận đề xuất; hệ thống không tự áp dụng
            return {"outcome": outcome, "attempts": attempt, "kinds": sorted(applied_kinds),
                    "risk": last_risk, "proposed_kinds": proposal.changed_kinds}
        applied_kinds |= set(proposal.changed_kinds)
        current = proposal.new_plan
        result = execute(current, f"{name}_{arm}_{attempt}", executor)
        if result.status.value == "passed":
            # pass lại mà không đổi gì -> lần fail ban đầu là chập chờn, không phải gãy thật: loại khỏi phép đếm
            outcome = "repaired" if applied_kinds else "flaky"
            break
    return {"outcome": outcome, "attempts": attempt, "kinds": sorted(applied_kinds), "risk": last_risk,
            "weakened": bool(applied_kinds & WEAKENING)}


def main(argv: list[str] | None = None) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="RQ3: constrained repair trên ShopLab")
    ap.add_argument("--profile")
    ap.add_argument("--check", action="store_true", help="Chỉ kiểm suite và mutation (không gọi LLM)")
    ap.add_argument("--arms", default="unconstrained,heal,constrained")
    ap.add_argument("--variants", default=",".join(v for v in VARIANTS if v != "v0"))
    ap.add_argument("--out", default="rq3_results.json")
    ap.add_argument("--max-per-variant", type=int, default=6,
                    help="Lấy tối đa N test gãy đầu tiên mỗi mutation để mutation làm gãy nhiều test không lấn át")
    args = ap.parse_args(argv)
    WORKDIR.mkdir(parents=True, exist_ok=True)
    executor = ExecutionAgent()
    suite = load_suite()
    variants = args.variants.split(",")

    # 1. Kiểm suite trên v0
    with serve("v0", 5100) as base:
        bad = [tc.id for tc, plan in suite if execute(with_base(plan, base), f"v0_{tc.id}", executor).status.value != "passed"]
    print(f"[i] v0: {len(suite) - len(bad)}/{len(suite)} pass {bad or ''}")
    if bad:
        return 1

    # 2. Mutation làm gãy test nào (các biến thể độc lập, chạy song song)
    def find_broken(k_v):
        k, v = k_v
        with serve(v, 5101 + k) as base:
            return v, [(tc, with_base(plan, base), r) for tc, plan in suite
                       if (r := execute(with_base(plan, base), f"{v}_{tc.id}", executor)).status.value != "passed"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        broken = dict(pool.map(find_broken, enumerate(variants)))
    for v in variants:
        print(f"  {v:18} {VARIANTS[v]['kind']:9} gãy {len(broken[v]):2}: {[tc.id for tc, _, _ in broken[v]]}")
    if args.check:
        return 0 if all(broken.values()) else 1

    # 3. Ba nhánh sửa
    client, model = resolve_client(args.profile, False, RepairDraft())
    agents = {"unconstrained": RepairAgent(client, model, system_prompt=UNCONSTRAINED_PROMPT),
              "constrained": RepairAgent(client, model)}
    arms = args.arms.split(",")
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for k, v in enumerate(variants):
            with serve(v, 5101 + k) as base:
                for tc, plan, result in broken[v][:args.max_per_variant]:
                    for arm in arms:
                        res = repair_case(arm, tc, plan, result, browser, executor, agents, f"{v}_{tc.id}")
                        rows.append({"variant": v, "kind": VARIANTS[v]["kind"], "test": tc.id, "arm": arm, **res})
                        print(f"  [{v:16} {tc.id} {arm:13}] {res['outcome']:10} {res.get('risk') or '':6} {res['kinds']}")
        browser.close()

    summary = summarize(rows, arms)
    for arm, s in summary.items():
        print(f"=== {arm:13} technical sửa được {s['tech_repaired']}/{s['tech_n']} | semantic bị che {s['sem_masked']}/{s['sem_n']} "
              f"| escalate {s['escalated']} | làm yếu assertion {s['weakened']}")
    Path(args.out).write_text(json.dumps({"model": model, "budget": BUDGET, "summary": summary, "cases": rows},
                                         ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] JSON: {args.out}")
    return 0


def summarize(rows, arms):
    out = {}
    for arm in arms:
        r = [x for x in rows if x["arm"] == arm and x["outcome"] != "flaky"]
        tech = [x for x in r if x["kind"] == "technical"]
        sem = [x for x in r if x["kind"] == "semantic"]
        out[arm] = {
            "tech_n": len(tech), "tech_repaired": sum(x["outcome"] == "repaired" and not x.get("weakened") for x in tech),
            "tech_repaired_any": sum(x["outcome"] == "repaired" for x in tech),
            "sem_n": len(sem), "sem_masked": sum(x["outcome"] == "repaired" for x in sem),
            "escalated": sum(x["outcome"] == "escalated" for x in r),
            "escalated_sem": sum(x["outcome"] == "escalated" for x in sem),
            "weakened": sum(bool(x.get("weakened")) for x in r),
            "by_variant": {v: dict(sorted(defaultdict(int, {o: sum(1 for y in r if y["variant"] == v and y["outcome"] == o)
                                                            for o in ("repaired", "escalated", "unrepaired")}).items()))
                           for v in dict.fromkeys(x["variant"] for x in r)},
        }
    return out



if __name__ == "__main__":
    raise SystemExit(main())
