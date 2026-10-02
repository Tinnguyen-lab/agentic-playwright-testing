"""Traceability Service (architecture v0.1, mục 5.10) — dựng & kiểm chuỗi truy vết.

Chain: Requirement -> TestCase -> (Script) -> Execution -> Repair. Thuần, tất định.
"""
from __future__ import annotations

from src.models.playwright_artifacts import ExecStatus, ExecutionResult
from src.models.repair import RepairProposal
from src.models.test_case import TestCase


def build_report(requirement_ids: list[str], test_cases: list[TestCase],
                 executions: list[ExecutionResult], repairs: list[RepairProposal]) -> dict:
    req_set = set(requirement_ids)
    tc_ids = {tc.id for tc in test_cases}
    execs_by_tc: dict[str, list[ExecutionResult]] = {}
    for e in executions:
        execs_by_tc.setdefault(e.test_case_id, []).append(e)
    repairs_by_tc: dict[str, list[RepairProposal]] = {}
    for r in repairs:
        repairs_by_tc.setdefault(r.test_case_id, []).append(r)

    covered_reqs = {tc.requirement_id for tc in test_cases if tc.requirement_id in req_set}
    executed_tcs = {tc.id for tc in test_cases if tc.id in execs_by_tc}

    chain = []
    for req in requirement_ids:
        req_tcs = [tc for tc in test_cases if tc.requirement_id == req]
        chain.append({
            "requirement_id": req,
            "test_cases": [{
                "id": tc.id,
                "executions": [e.status.value for e in execs_by_tc.get(tc.id, [])],
                "repairs": [{"outcome": r.outcome.value, "risk": r.risk_level.value} for r in repairs_by_tc.get(tc.id, [])],
            } for tc in req_tcs],
        })

    total_exec = len(executions)
    passed = sum(1 for e in executions if e.status == ExecStatus.PASSED)
    return {
        "n_requirements": len(requirement_ids),
        "n_test_cases": len(test_cases),
        "n_executions": total_exec,
        "n_repairs": len(repairs),
        "requirement_coverage": len(covered_reqs) / len(req_set) if req_set else 0.0,
        "executed_coverage": len(executed_tcs) / len(tc_ids) if tc_ids else 0.0,
        "pass_rate": passed / total_exec if total_exec else 0.0,
        "orphans": {
            "test_cases": sorted(tc.id for tc in test_cases if tc.requirement_id not in req_set),
            "executions": sorted({e.test_case_id for e in executions if e.test_case_id not in tc_ids}),
            "repairs": sorted({r.test_case_id for r in repairs if r.test_case_id not in tc_ids}),
        },
        "chain": chain,
    }


def render_markdown(report: dict) -> str:
    out = ["# Traceability report\n",
           f"- Requirement: {report['n_requirements']} | Test case: {report['n_test_cases']} "
           f"| Execution: {report['n_executions']} | Repair: {report['n_repairs']}",
           f"- Requirement coverage: {report['requirement_coverage']:.0%} "
           f"| Executed coverage: {report['executed_coverage']:.0%} | Pass rate: {report['pass_rate']:.0%}\n"]
    orph = report["orphans"]
    if any(orph.values()):
        out.append(f"⚠ Orphan — test_cases: {orph['test_cases']} | executions: {orph['executions']} | repairs: {orph['repairs']}\n")
    out.append("## Chain Requirement → TestCase → Execution → Repair\n")
    for node in report["chain"]:
        out.append(f"- **{node['requirement_id']}**")
        for tc in node["test_cases"]:
            ex = ", ".join(tc["executions"]) or "—"
            rp = ", ".join(f"{r['outcome']}/{r['risk']}" for r in tc["repairs"]) or "—"
            out.append(f"  - {tc['id']} | exec: {ex} | repair: {rp}")
        if not node["test_cases"]:
            out.append("  - (chưa có test case)")
    return "\n".join(out) + "\n"
