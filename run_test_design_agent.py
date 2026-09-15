"""CLI Test Design Agent: từ kết quả Requirement Agent (result.json) sinh test case.

    # offline:
    python run_test_design_agent.py --from result.json --approve-all --mock
    # thật (local/cloud):
    python run_test_design_agent.py --from result.json --approve-all --profile cloud
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.agents.test_design_agent import TestDesignAgent
from src.evaluation.design_metrics import coverage_report
from src.models.approval import ApprovalDecision, ApprovalStatus, is_approved
from src.models.requirement import RequirementAnalysisResult
from src.models.test_case import TestCase, TestCaseDraft, TestStep, TestType
from src.utils.cli import resolve_client


def default_mock_draft() -> TestCaseDraft:
    return TestCaseDraft(test_cases=[
        TestCase(
            title="Luồng hợp lệ", type=TestType.POSITIVE,
            steps=[TestStep(action="Thực hiện action với dữ liệu hợp lệ", expected="Đạt expected_outcome")],
            expected_result="Hệ thống phản hồi đúng như yêu cầu",
        ),
        TestCase(
            title="Dữ liệu không hợp lệ", type=TestType.NEGATIVE,
            steps=[TestStep(action="Thực hiện action với dữ liệu sai", expected="Báo lỗi")],
            expected_result="Hệ thống báo lỗi và không thực hiện",
        ),
    ])


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Test Design Agent")
    ap.add_argument("--from", dest="src", required=True, help="result.json của Requirement Agent")
    ap.add_argument("--approve-all", action="store_true",
                    help="Mô phỏng người dùng phê duyệt toàn bộ requirement (AG-01)")
    ap.add_argument("--mock", action="store_true", help="LLM giả lập (offline)")
    ap.add_argument("--profile", help="Hồ sơ .env: 'cloud' -> .env.cloud")
    ap.add_argument("--out", default="test_design.json", help="File JSON đầu ra")
    args = ap.parse_args(argv)

    req_result = RequirementAnalysisResult.model_validate_json(Path(args.src).read_text(encoding="utf-8"))

    decisions: list[ApprovalDecision] = []
    if args.approve_all:
        decisions = [
            ApprovalDecision(artifact_id=r.id, status=ApprovalStatus.APPROVED, decided_by="cli --approve-all")
            for r in req_result.requirements
        ]
    approved = [r for r in req_result.requirements if is_approved(decisions, r.id)]
    if not approved:
        print("[!] Chưa có requirement nào approved. Thêm --approve-all để mô phỏng phê duyệt (AG-01).")
        return 1

    client, model_name = resolve_client(args.profile, args.mock, default_mock_draft())
    agent = TestDesignAgent(client, model_name=model_name)

    all_cases: list[TestCase] = []
    all_links = []
    results = []
    for req in approved:
        res = agent.design(req)
        results.append(res)
        all_cases.extend(res.test_cases)
        all_links.extend(res.trace_links)

    print(f"\n=== TEST DESIGN: {req_result.source_name} | model={model_name} ===")
    print(f"Requirement approved: {len(approved)} | Tổng test case: {len(all_cases)}\n")
    for res in results:
        print(f"[{res.source_requirement_id}] -> {len(res.test_cases)} case | loại: {', '.join(res.type_coverage) or '—'}")
        for tc in res.test_cases:
            print(f"    {tc.id} [{tc.type.value}] {tc.title}")

    cov = coverage_report(results, [r.id for r in approved])
    print(f"\nCoverage: {cov['requirement_coverage']:.0%} requirement có test "
          f"| trace {cov['trace_completeness']:.0%} | loại: {', '.join(cov['types_covered']) or '—'}")
    if cov["uncovered_requirements"]:
        print(f"  ⚠ chưa có test: {', '.join(cov['uncovered_requirements'])}")

    out = {
        "source": req_result.source_name,
        "model_used": model_name,
        "coverage": cov,
        "approvals": [d.model_dump(mode="json") for d in decisions],
        "test_cases": [tc.model_dump(mode="json") for tc in all_cases],
        "trace_links": [link.model_dump(mode="json") for link in all_links],
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[✓] Đã ghi: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
